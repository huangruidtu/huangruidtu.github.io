---
title: 从一次构建到一次可回滚的发布：Edge CI/CD 复盘
date: 2026-11-16
summary: 第一次把「交付」当成一个完整的问题来做：分层的 DevSecOps 流水线、私网里的 self-hosted runner、以 S3 为中心的版本化产物，以及一个手动触发的回滚。
series: 项目复盘
series_part: 1
---

> 「项目复盘」系列第一篇。这个系列按我自己理解的演进顺序，一个项目一篇，记录每个项目做了什么、为什么这么做，以及做完之后想法是怎么变的。
>
> 项目地址：[huangruidtu/edge-ci-cd-demo](https://github.com/huangruidtu/edge-ci-cd-demo)

从这个项目开始，是因为它是我第一次把「交付」当成一个完整的问题来做，而不只是写一个能跑通的 workflow 文件。

## 起点：一个几乎什么都不做的程序

应用本身刻意做得很简单，`main.cpp` 只打印一行 `CI/CD Demo Running!`。应用越简单，注意力就越能放在交付链路本身。

真正有约束的是目标设备：局域网里的一块老板子，ARMv7，跑的是 **Ubuntu 14.04**。它不跑容器，吃的是原生二进制；它在私网里，公网上的 CI 连不到它。后面几乎所有的设计决策，都是被这两个约束推着走的。

整个项目分三天推进，每一步都对应一个真实的问题，而不是一开始就写一个巨大的 workflow。

## Day 1：先让 CI 能「失败」

第一天的工作很常规：C++ 项目骨架、CMake、多阶段 Dockerfile、GitHub Actions、`dev` / `main` / PR 的分支策略、推镜像到 ECR。

有一个小动作我觉得值得记一下。提交历史里有两条：

```text
Test: break CI intentionally
Fix: restore CI
```

`main.cpp` 里至今还留着一段被 `#if 1` 关掉的代码：

```cpp
int main() {
    int *p = nullptr;
    *p = 10;   // null pointer dereference
    return 0;
}
```

我把开关切过去，看 cppcheck 会不会把流水线拦下来。一个从来没红过的 CI，你其实不知道它到底有没有在检查东西。先确认它**会失败**，再相信它**通过了**。

另一个早期决定是镜像标签。一开始用 commit SHA，第二天改成了 release 用语义化版本（`v1.2.4` 这种）：SHA 负责可追溯，版本号负责给人看、也给后面的回滚当索引。`latest` 从头到尾没用过。

## Day 2：安全检查要分层，而不是堆在一起

第二天把 CI 加固成了一个分层的 DevSecOps 流水线：

| 触发点 | 目的 | 跑什么 |
|---|---|---|
| `dev` 分支 | 快速反馈 | 只跑 cppcheck（SAST） |
| PR / `main` | 质量与安全门禁 | cppcheck + Docker build + Trivy FS + Trivy image |
| tag `vX.Y.Z` | 发布与交付 | 构建版本化产物、发布、部署 |

Trivy 两个扫描都设置了 `severity: HIGH,CRITICAL` 和 `exit-code: 1`。也就是说安全检查是**拦截**，不是**报告**。只出报告不拦截的扫描，很快就会变成没人看的噪音。

为什么不每个分支都跑全量？因为全量跑在 `dev` 上，日常迭代会被拖慢，大家就会想办法绕开它。为什么不只在发布时跑？因为问题发现得太晚。分层的意思是：越接近发布，检查越严格。

同一天还加了 Dependabot。我对它的理解是：扫描负责**发现**风险，Dependabot 负责**推动修复**。策略也很简单：patch 直接合，minor 合完靠 CI 兜底，major 要手动验证。另外加了 Docker layer cache，让 PR 上的构建别每次从零开始。

## Day 3：CD 真正难的地方不在 YAML 里

第三天要把二进制真正送到板子上。这一天打了 9 个 tag（`v1.2.1` 到 `v1.3.1`），基本上每个 tag 都是一次「以为好了，结果没有」。回头看，有四个转折点。

**1. 先交叉编译。** 最直接的思路：在 GitHub-hosted runner 上装 `gcc-arm-linux-gnueabihf`，交叉编译出 ARMv7 二进制，按版本上传到 S3。

**2. 部署写进 build job，然后发现连不上。** 第一版 CD 直接在 build job 里 `scp` + `ssh` 到板子上。问题是板子在私网，GitHub 的云端 runner 根本够不着它。于是把部署拆成一个独立的 job，跑在局域网里的 **self-hosted runner** 上。

**3. 新工具链和老系统。** 二进制送到了，但 Ubuntu 14.04 太老了，新工具链编出来的东西在上面有运行时兼容问题。我把 ARM 产物的构建也挪到了 self-hosted runner 上，还试过把 `CMakeLists.txt` 的最低版本从 3.10 降到 2.8.12（workflow 里这一步的名字就叫 *legacy compatibility attempt*）。

**4. 临时关掉 ECR。** 设备吃的是二进制，不是镜像。在这条交付路径上，往 ECR 推镜像只是噪音，就先关掉了。

最后的交付链路其实是两条路径：

```text
push / PR / tag --> GitHub-hosted runner
                    cppcheck -> Docker build -> Trivy FS -> Trivy image

tag --------------> self-hosted runner (局域网内)
                    构建版本化二进制 -> 上传 S3
                    -> 从 S3 下载 -> scp 到板子 -> stop.sh / start.sh
```

中间那个 S3 很关键。产物路径是：

```text
s3://edge-cicd-demo-artifacts/edge-demo/releases/<version>/edge-app
```

构建只管往这里放，部署只管从这里拿。两边不需要知道对方怎么实现，S3 就是版本的「事实来源」。这个设计后面直接让回滚变得很简单。

## 回滚：一个单独的、手动触发的 workflow

回滚没有塞进主流水线，而是一个独立的 `workflow_dispatch`，输入一个版本号：

```yaml
on:
  workflow_dispatch:
    inputs:
      release_version:
        description: 'Release version to roll back to (e.g. v1.2.4)'
        required: true
```

逻辑跟正常部署完全一样：从 S3 拿那个版本的二进制、拷到板子上、调用设备上已有的 `stop.sh` / `start.sh`。因为每个版本都还在 S3 里，回滚就是「重新部署一个旧版本」，不需要任何额外机制。

为什么是手动？回滚是一个敏感的运维动作，我希望它是**显式的**，由人来决定什么时候做、退到哪个版本。

## 一个后来反复用到的想法

这个项目最终并没有完全解决老板子的运行时兼容问题。我在文档里把它写成了一个单独的、平台相关的问题，而不是去说「CI/CD 失败了」：

> CI/CD orchestration success and target runtime compatibility are not the same problem.

当时这么写，多少有点给自己找台阶的意思。但后来我越来越觉得这是一个很重要的工程习惯：**分清楚「我证明了什么」和「我没证明什么」**。流水线的编排是对的、产物确实构建出来了、确实发布了、确实送到了设备上，这些都成立；板子的运行时兼容是另一件事，不应该把两件事混成一句「做完了」或者「没做完」。

这个想法在后面的项目里会越来越明确，到后来的平台项目和数据项目里，我直接单独写了一份文档，列出哪些东西是真正跑过验证的，哪些只是设计和静态验证过的。

## 如果现在再做一次

项目文档里自己列过的后续方向：

- 镜像签名（Cosign）和 SBOM，让「产物是谁、从哪来」可验证
- 用 SARIF 把扫描结果上报到 GitHub Security，而不只是看日志
- 渐进式发布，而不是一次性替换

回头看还想补的：

- AWS 凭证现在用的是存在 GitHub Secrets 里的长期 Access Key，应该换成 GitHub OIDC + STS 的短期凭证
- 部署完调用了 `start.sh` 就结束了，缺一个部署后的健康检查。有了健康检查，才谈得上自动回滚

## 下一篇

下一篇写 CPEmon 的第一个版本：一个在自建 Kubernetes 上、从头到尾自己运维的 CPE 监控 MVP。那是我第一次面对「所有东西都得自己管」意味着什么。
