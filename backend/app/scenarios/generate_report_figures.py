"""
Generates high-resolution academic figures for the TrueTrace final project report.
Saves PNG figures into docs/figures/ directory.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]


def fig_1_1_overapproximation():
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)

    # Host side box
    rect_host = patches.FancyBboxPatch((0.5, 2.2), 3.8, 2.2, boxstyle="round,pad=0.2",
                                       fc="#f1f5f9", ec="#1e293b", lw=1.5)
    ax.add_patch(rect_host)
    ax.text(2.4, 4.1, "Host Operating System", fontsize=11, fontweight="bold", ha="center", color="#0f172a")
    ax.text(2.4, 3.5, "Process: mimikatz.exe (PID 1024)\nSystem Call: write(sock, buf, 4096)\nReturn Code: 4096 (SUCCESS)",
            fontsize=8.5, ha="center", va="center", color="#334155",
            bbox=dict(boxstyle="square,pad=0.3", fc="#e2e8f0", ec="#94a3b8", lw=0.8))
    ax.text(2.4, 2.5, "Data accepted into kernel socket buffer", fontsize=8, ha="center", style="italic", color="#64748b")

    # Arrow to network
    ax.annotate("", xy=(5.2, 3.3), xytext=(4.4, 3.3),
                arrowprops=dict(arrowstyle="->", lw=2, color="#0284c7"))
    ax.text(4.8, 3.5, "NIC Wire\nTransit", fontsize=7.5, ha="center", color="#0369a1")

    # Network reality box
    rect_net = patches.FancyBboxPatch((5.4, 0.5), 4.2, 4.0, boxstyle="round,pad=0.2",
                                      fc="#f8fafc", ec="#0284c7", lw=1.5)
    ax.add_patch(rect_net)
    ax.text(7.5, 4.2, "Physical Network Reality", fontsize=11, fontweight="bold", ha="center", color="#0369a1")

    # Three paths
    # Path 1: Delivered
    rect_p1 = patches.FancyBboxPatch((5.6, 2.9), 3.8, 0.9, boxstyle="round,pad=0.1",
                                     fc="#ecfdf5", ec="#10b981", lw=1)
    ax.add_patch(rect_p1)
    ax.text(5.8, 3.35, "Case A: Delivered (SUPPORTED)", fontsize=8.5, fontweight="bold", color="#065f46")
    ax.text(5.8, 3.05, "TCP 3-way handshake + ACKs acknowledged", fontsize=7.5, color="#047857")

    # Path 2: Blocked / RST
    rect_p2 = patches.FancyBboxPatch((5.6, 1.7), 3.8, 0.9, boxstyle="round,pad=0.1",
                                     fc="#fef2f2", ec="#ef4444", lw=1)
    ax.add_patch(rect_p2)
    ax.text(5.8, 2.15, "Case B: Blocked / Reset (CONTRADICTED)", fontsize=8.5, fontweight="bold", color="#991b1b")
    ax.text(5.8, 1.85, "TCP RST/ACK (Port Closed) or Firewall Drop", fontsize=7.5, color="#b91c1c")

    # Path 3: Unobservable
    rect_p3 = patches.FancyBboxPatch((5.6, 0.6), 3.8, 0.9, boxstyle="round,pad=0.1",
                                     fc="#fffbeb", ec="#f59e0b", lw=1)
    ax.add_patch(rect_p3)
    ax.text(5.8, 1.05, "Case C: Blindspot (UNRESOLVED)", fontsize=8.5, fontweight="bold", color="#92400e")
    ax.text(5.8, 0.75, "Unmonitored subnet / packet loss on tap", fontsize=7.5, color="#b45309")

    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig_1_1_overapproximation.png"), dpi=300)
    plt.close(fig)


def fig_3_1_architecture():
    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)

    # 1. Inputs
    ax.text(1.2, 5.6, "Evidence Ingestion", fontsize=10, fontweight="bold", ha="center", color="#1e293b")
    rect_in1 = patches.FancyBboxPatch((0.2, 3.8), 2.0, 1.4, boxstyle="round,pad=0.1", fc="#f1f5f9", ec="#64748b", lw=1.2)
    ax.add_patch(rect_in1)
    ax.text(1.2, 4.6, "Host Audit Logs\n(Linux auditd, Sysmon,\nDARPA TC CDM)", fontsize=8, ha="center", va="center")

    rect_in2 = patches.FancyBboxPatch((0.2, 1.2), 2.0, 1.4, boxstyle="round,pad=0.1", fc="#f1f5f9", ec="#64748b", lw=1.2)
    ax.add_patch(rect_in2)
    ax.text(1.2, 1.9, "Packet Captures\n(PCAP / PCAPNG\nNetwork Wire Frames)", fontsize=8, ha="center", va="center")

    # 2. Parsers & Claim Synthesis
    rect_p1 = patches.FancyBboxPatch((2.8, 3.8), 2.2, 1.4, boxstyle="round,pad=0.1", fc="#e0f2fe", ec="#0284c7", lw=1.2)
    ax.add_patch(rect_p1)
    ax.text(3.9, 4.6, "Host Log Parser &\nCandidate Claim\nSynthesis Engine", fontsize=8, ha="center", va="center", color="#0369a1")

    rect_p2 = patches.FancyBboxPatch((2.8, 1.2), 2.2, 1.4, boxstyle="round,pad=0.1", fc="#e0f2fe", ec="#0284c7", lw=1.2)
    ax.add_patch(rect_p2)
    ax.text(3.9, 1.9, "PCAP L3/L4 Parser\n(TCP Flags, Seq/Ack,\nPayload Length)", fontsize=8, ha="center", va="center", color="#0369a1")

    # Arrows to central engine
    ax.annotate("", xy=(2.7, 4.5), xytext=(2.3, 4.5), arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748b"))
    ax.annotate("", xy=(2.7, 1.9), xytext=(2.3, 1.9), arrowprops=dict(arrowstyle="->", lw=1.5, color="#64748b"))

    # 3. Observability Matrix & Matching
    rect_core = patches.FancyBboxPatch((5.6, 1.0), 2.6, 4.4, boxstyle="round,pad=0.15", fc="#f8fafc", ec="#1e3a8a", lw=2)
    ax.add_patch(rect_core)
    ax.text(6.9, 5.1, "TrueTrace Engine", fontsize=10, fontweight="bold", ha="center", color="#1e3a8a")

    rect_sub1 = patches.FancyBboxPatch((5.8, 3.8), 2.2, 0.9, boxstyle="round,pad=0.1", fc="#ffffff", ec="#94a3b8", lw=0.8)
    ax.add_patch(rect_sub1)
    ax.text(6.9, 4.25, "Observability Matrix\n(CIDR, Window, Loss)", fontsize=7.5, ha="center", va="center")

    rect_sub2 = patches.FancyBboxPatch((5.8, 2.5), 2.2, 0.9, boxstyle="round,pad=0.1", fc="#ffffff", ec="#94a3b8", lw=0.8)
    ax.add_patch(rect_sub2)
    ax.text(6.9, 2.95, "5-Tuple Directional\nFlow Correlator", fontsize=7.5, ha="center", va="center")

    rect_sub3 = patches.FancyBboxPatch((5.8, 1.2), 2.2, 0.9, boxstyle="round,pad=0.1", fc="#ffffff", ec="#94a3b8", lw=0.8)
    ax.add_patch(rect_sub3)
    ax.text(6.9, 1.65, "Invariant Arbitration\n(Rules & Preconditions)", fontsize=7.5, ha="center", va="center")

    ax.annotate("", xy=(5.5, 4.5), xytext=(5.1, 4.5), arrowprops=dict(arrowstyle="->", lw=1.5, color="#0284c7"))
    ax.annotate("", xy=(5.5, 1.9), xytext=(5.1, 1.9), arrowprops=dict(arrowstyle="->", lw=1.5, color="#0284c7"))

    # 4. Outputs
    rect_out1 = patches.FancyBboxPatch((8.8, 3.4), 2.0, 1.8, boxstyle="round,pad=0.1", fc="#ecfdf5", ec="#059669", lw=1.5)
    ax.add_patch(rect_out1)
    ax.text(9.8, 4.7, "Refined Attack Graph", fontsize=8.5, fontweight="bold", ha="center", color="#065f46")
    ax.text(9.8, 3.9, "- Supported: Retained\n- Contradicted: Pruned\n- Unresolved: Preserved", fontsize=7.5, ha="center", color="#047857")

    rect_out2 = patches.FancyBboxPatch((8.8, 1.2), 2.0, 1.5, boxstyle="round,pad=0.1", fc="#f1f5f9", ec="#334155", lw=1.2)
    ax.add_patch(rect_out2)
    ax.text(9.8, 2.15, "Forensic Evidence\nReport & SHA-256\nProvenance Export", fontsize=8, fontweight="bold", ha="center", color="#0f172a")
    ax.text(9.8, 1.5, "(Markdown / JSON)", fontsize=7, ha="center", color="#475569")

    ax.annotate("", xy=(8.7, 4.3), xytext=(8.3, 4.3), arrowprops=dict(arrowstyle="->", lw=1.5, color="#059669"))
    ax.annotate("", xy=(8.7, 1.9), xytext=(8.3, 1.9), arrowprops=dict(arrowstyle="->", lw=1.5, color="#334155"))

    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig_3_1_architecture.png"), dpi=300)
    plt.close(fig)


def fig_4_1_observability_flow():
    fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)

    # Decision diamonds / boxes
    # Start: Claim C
    box_start = patches.FancyBboxPatch((0.5, 3.5), 1.8, 0.9, boxstyle="round,pad=0.1", fc="#e2e8f0", ec="#475569", lw=1.2)
    ax.add_patch(box_start)
    ax.text(1.4, 3.95, "Candidate Claim C\n(src, dst, time tc)", fontsize=8, ha="center", va="center", fontweight="bold")

    # Q1: In Monitored CIDR?
    box_q1 = patches.FancyBboxPatch((3.0, 3.3), 2.2, 1.3, boxstyle="round,pad=0.1", fc="#fef3c7", ec="#d97706", lw=1.2)
    ax.add_patch(box_q1)
    ax.text(4.1, 3.95, "Is flow IP in\nSensor Monitored\nCIDRs?", fontsize=8, ha="center", va="center", fontweight="bold")

    ax.annotate("", xy=(2.9, 3.95), xytext=(2.4, 3.95), arrowprops=dict(arrowstyle="->", lw=1.5))

    # Q1 No -> UNOBSERVABLE
    box_unobs = patches.FancyBboxPatch((3.0, 1.0), 2.2, 1.0, boxstyle="round,pad=0.1", fc="#fee2e2", ec="#dc2626", lw=1.2)
    ax.add_patch(box_unobs)
    ax.text(4.1, 1.5, "UNOBSERVABLE\n(Verdict: UNRESOLVED)\nAbsence != Proof", fontsize=8, ha="center", va="center", fontweight="bold", color="#991b1b")
    ax.annotate("NO", xy=(4.1, 2.1), xytext=(4.1, 3.2), arrowprops=dict(arrowstyle="->", lw=1.5, color="#dc2626"), ha="center", fontsize=8, fontweight="bold", color="#dc2626")

    # Q1 Yes -> Q2: In Capture Window?
    box_q2 = patches.FancyBboxPatch((6.0, 3.3), 2.0, 1.3, boxstyle="round,pad=0.1", fc="#fef3c7", ec="#d97706", lw=1.2)
    ax.add_patch(box_q2)
    ax.text(7.0, 3.95, "Is tc inside\n[Tstart, Tend]\nof sensor?", fontsize=8, ha="center", va="center", fontweight="bold")
    ax.annotate("YES", xy=(5.9, 3.95), xytext=(5.3, 3.95), arrowprops=dict(arrowstyle="->", lw=1.5, color="#059669"), va="bottom", fontsize=8, fontweight="bold", color="#059669")

    # Q2 No -> UNOBSERVABLE
    ax.annotate("NO", xy=(5.3, 1.5), xytext=(6.5, 3.2), arrowprops=dict(arrowstyle="->", lw=1.5, color="#dc2626"), fontsize=8, fontweight="bold", color="#dc2626")

    # Q2 Yes -> Q3: Packet Loss?
    box_q3 = patches.FancyBboxPatch((8.6, 2.8), 1.2, 2.0, boxstyle="round,pad=0.1", fc="#f1f5f9", ec="#334155", lw=1.2)
    ax.add_patch(box_q3)
    ax.text(9.2, 4.2, "Hardware\nLoss?", fontsize=8, ha="center", fontweight="bold")
    ax.text(9.2, 3.4, "Loss=True\n-> DEGRADED\n(UNRESOLVED)", fontsize=7, ha="center", color="#b45309")
    ax.text(9.2, 2.3, "Loss=False\n-> FULLY\nOBSERVABLE", fontsize=7, ha="center", color="#065f46")
    ax.annotate("YES", xy=(8.5, 3.95), xytext=(8.1, 3.95), arrowprops=dict(arrowstyle="->", lw=1.5, color="#059669"), va="bottom", fontsize=8, fontweight="bold", color="#059669")

    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig_4_1_observability_flow.png"), dpi=300)
    plt.close(fig)


def fig_5_1_gantt_chart():
    fig, ax = plt.subplots(figsize=(9.0, 4.0), dpi=300)
    
    tasks = [
        "1. Problem Formulation & Literature Review",
        "2. Trace Dataset Analysis (DARPA TC CDM)",
        "3. Verification Engine Design & Rules Spec",
        "4. PCAP & Host Log Parser Engineering",
        "5. SQLite Persistence & REST API Layer",
        "6. React Forensics Workbench (@xyflow/react)",
        "7. Controlled Experiments & Live Sockets",
        "8. Empirical Evaluation & Final Report"
    ]
    starts = [1, 3, 5, 6, 8, 9, 11, 13]
    durations = [3, 3, 2, 3, 3, 3, 2, 2]
    colors = ["#1e3a8a", "#1d4ed8", "#2563eb", "#0284c7", "#059669", "#10b981", "#d97706", "#7c3aed"]

    y_pos = np.arange(len(tasks))
    ax.barh(y_pos, durations, left=starts, align="center", color=colors, alpha=0.85, height=0.55, edgecolor="#0f172a", lw=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(tasks, fontsize=8.5, fontweight="bold", color="#1e293b")
    ax.invert_yaxis()
    ax.set_xlabel("Project Timeline (Weeks - Academic Term Fall 2026-27)", fontsize=9.5, fontweight="bold", color="#0f172a")
    ax.set_xlim(0, 15)
    ax.set_xticks(range(1, 15))
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig_5_1_gantt_chart.png"), dpi=300)
    plt.close(fig)


def fig_7_1_confusion_matrix():
    fig, ax = plt.subplots(figsize=(5.5, 4.5), dpi=300)
    
    cm = np.array([
        [2, 0, 0],
        [0, 2, 0],
        [0, 0, 4]
    ])
    classes = ["Supported", "Contradicted", "Unresolved"]

    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=8)

    ax.set_xticks(np.arange(len(classes)))
    ax.set_yticks(np.arange(len(classes)))
    ax.set_xticklabels(classes, fontsize=9, fontweight="bold", color="#0f172a")
    ax.set_yticklabels(classes, fontsize=9, fontweight="bold", color="#0f172a")

    ax.set_xlabel("Predicted Verdict", fontsize=10, fontweight="bold", labelpad=8)
    ax.set_ylabel("Ground-Truth Label", fontsize=10, fontweight="bold", labelpad=8)
    ax.set_title("TrueTrace Benchmark Confusion Matrix", fontsize=11, fontweight="bold", pad=12)

    # Loop over data dimensions and create text annotations
    for i in range(len(classes)):
        for j in range(len(classes)):
            val = cm[i, j]
            color = "white" if val > 1 else "black"
            ax.text(j, i, format(val, "d"),
                    ha="center", va="center",
                    color=color, fontsize=12, fontweight="bold")

    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig_7_1_confusion_matrix.png"), dpi=300)
    plt.close(fig)


def fig_7_2_metrics_bar():
    fig, ax = plt.subplots(figsize=(6.5, 3.8), dpi=300)
    
    classes = ["Supported", "Contradicted", "Unresolved", "Macro Average"]
    precision = [1.0, 1.0, 1.0, 1.0]
    recall = [1.0, 1.0, 1.0, 1.0]
    f1 = [1.0, 1.0, 1.0, 1.0]

    x = np.arange(len(classes))
    width = 0.25

    rects1 = ax.bar(x - width, precision, width, label="Precision", color="#0284c7", edgecolor="#0f172a", lw=0.8)
    rects2 = ax.bar(x, recall, width, label="Recall", color="#10b981", edgecolor="#0f172a", lw=0.8)
    rects3 = ax.bar(x + width, f1, width, label="F1-Score", color="#8b5cf6", edgecolor="#0f172a", lw=0.8)

    ax.set_ylabel("Score (0.0 to 1.0)", fontsize=9.5, fontweight="bold")
    ax.set_title("Empirical Evaluation Metrics Across Invariant Verdict Classes", fontsize=10.5, fontweight="bold", pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(classes, fontsize=8.5, fontweight="bold")
    ax.set_ylim(0, 1.25)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for r in rects1 + rects2 + rects3:
        h = r.get_height()
        ax.annotate(f"{h:.2f}",
                    xy=(r.get_x() + r.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, "fig_7_2_metrics_bar.png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig_1_1_overapproximation()
    fig_3_1_architecture()
    fig_4_1_observability_flow()
    fig_5_1_gantt_chart()
    fig_7_1_confusion_matrix()
    fig_7_2_metrics_bar()
    print("All report figures generated successfully in docs/figures!")
