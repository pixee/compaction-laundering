# References

1. **Straiker.** Claude Code Source Leak: Compaction as a Memory-Poisoning Channel. Technical
   writeup, 2026. Describes the laundered-through-summarization mechanism against Claude Code and
   names the code-execution risk; provides no runtime evidence, measured rates, or controls.

2. Pritam Dash, Tongyu Ge, Aditi Jain, Tanmay Shah, Zhiwei Shang. **From Untrusted Input to Trusted
   Memory: A Systematic Study of Memory Poisoning Attacks in LLM Agents.** arXiv:2606.04329, 2026.
   The systematic academic treatment: names compaction as a memory-write channel and
   source-attribution failure as the flaw; measures attack success at the memory write (~50%) but
   not through to behavior. Tested on research agents rather than released ones.

3. Sidharth Pulipaka, Stanislau Hlebik, Leonidas Raghav, Sahar Abdelnabi, Vyas Raina, Ivaxi Sheth,
   Mario Fritz. **Hidden in Memory: Sleeper Memory Poisoning in LLM Agents.** arXiv:2605.15338, 2026.
   Follows poisoned memory through to tool execution and exfiltration (60–89% success) via a dedicated
   persistent-memory module; does not cover compaction (confirmed by the authors).

4. Xuanye Zhang, Yongsen Zheng, Zhuqin Xu, Kaiyu Zhou, Bowen Shen, Haoran Ou, Tianwei Zhang,
   Kwok-Yan Lam. **MemMorph: Tool Hijacking in LLM Agents via Memory Poisoning.** arXiv:2605.26154,
   2026. Demonstrates memory poisoning through to execution (85.9%) in the persistent-memory channel.

5. Zesen Liu, Zihan Zhang, Dongdong She. **Safe to Check, Unsafe to Use: Relinking at the Compression
   Boundary of LLM Agents.** arXiv:2606.21732, 2026. A summarizer stitching several innocent fragments
   into one malicious instruction — a class our canaries cannot express.

6. Shiyang Chen. **Governance Decay: How Context Compaction Silently Erases Safety Constraints in
   Long-Horizon LLM Agents.** arXiv:2606.22528, 2026. Safety constraints disappearing across
   compaction, rather than a forged one surviving it.

7. Yedidel Louck. **Securing LLM-Agent Long-Term Memory Against Poisoning: Non-Malleable,
   Origin-Bound Authority with Machine-Checked Guarantees.** arXiv:2606.24322, 2026. An origin-binding
   defense for long-term memory; closely related to our provenance-contrast check, aimed at the
   persistent-memory channel.

8. **OWASP Foundation.** OWASP Top 10 for Agentic Applications (2026). Memory & Context
   Poisoning appears as a named category, with guidance to attach provenance to every memory write.

9. **Earendil Works.** pi — a coding agent. Open source, v0.79.0, commit `9b3a205`.
   <https://github.com/earendil-works/pi>

10. **Anthropic.** Anthropic Quickstarts: Computer Use Demo. Container image and reference
    sampling loop. <https://github.com/anthropics/anthropic-quickstarts>
