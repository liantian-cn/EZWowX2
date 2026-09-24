# 历史性能记录

以下为早期技术背景中的原记录，循环频率尚未确定的描述已被当前新帧驱动架构取代；这里不定义当前频率。

## Python loop

Each Python cycle captures the matrix, updates condition instances, evaluates the pre-parsed whitelist AST in rotation order, and sends at most one key. A cycle with no match sends nothing.

The loop frequency is intentionally undecided. Measure capture, decode, UI, and input costs before selecting it. A local microbenchmark showed that evaluating 30 small pre-parsed AST expressions at 10 Hz is negligible compared with image capture, so do not optimize the expression evaluator at the cost of clarity.
