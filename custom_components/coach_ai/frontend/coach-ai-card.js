class CoachAICard extends HTMLElement {

  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {

    const score =
      Number(
        hass.states["sensor.coach_ai_coach_score"]?.state
      ) || 0;

    const recovery =
      hass.states["sensor.coach_ai_recovery_score"]?.state ?? "--";

    const fatigue =
      hass.states["sensor.coach_ai_fatigue"]?.state ?? "--";

    const fitness =
      hass.states["sensor.coach_ai_fitness"]?.state ?? "--";

    const workout =
      hass.states["sensor.coach_ai_workout"]?.state ?? "--";

    const duration =
      hass.states["sensor.coach_ai_workout_duration"]?.state ?? "--";

    const zone =
      hass.states["sensor.coach_ai_training_zone"]?.state ?? "-";

    const tss =
      hass.states["sensor.coach_ai_target_tss"]?.state ?? "0";

    let color = "#ef4444";
    let status = "REST";

    if (score >= 80) {
      color = "#22c55e";
      status = "READY TO TRAIN";
    }
    else if (score >= 60) {
      color = "#eab308";
      status = "TRAIN";
    }
    else if (score >= 40) {
      color = "#f97316";
      status = "RECOVERY";
    }

    const circumference = 326.7;

    const offset =
      circumference -
      (score * circumference / 100);

    if (!this.content) {

      const card = document.createElement("ha-card");

      card.style.cssText = `
        border-radius:24px;
        overflow:hidden;
        background:#111827;
        color:white;
        padding:24px;
      `;

      this.content = document.createElement("div");

      card.appendChild(this.content);

      this.appendChild(card);

    }

    this.content.innerHTML = `

<div style="
text-align:center;
font-size:15px;
letter-spacing:4px;
color:#9ca3af;
margin-bottom:20px;
">

COACH AI

</div>

<div style="
display:flex;
justify-content:center;
">

<div style="
position:relative;
width:170px;
height:170px;
">

<svg
viewBox="0 0 120 120"
width="170"
height="170"
style="transform:rotate(-90deg);">

<circle
cx="60"
cy="60"
r="52"
fill="none"
stroke="#263041"
stroke-width="10"/>

<circle
cx="60"
cy="60"
r="52"
fill="none"
stroke="${color}"
stroke-width="10"
stroke-linecap="round"
stroke-dasharray="${circumference}"
stroke-dashoffset="${offset}"
style="
transition:all .7s ease;
"/>

</svg>

<div style="
position:absolute;
top:50%;
left:50%;
transform:translate(-50%,-50%);
text-align:center;
">

<div style="
font-size:46px;
font-weight:700;
color:${color};
">

${score}

</div>

<div style="
font-size:12px;
letter-spacing:2px;
color:#9ca3af;
">

COACH SCORE

</div>

</div>

</div>

</div>

<div style="
margin-top:12px;
text-align:center;
font-size:22px;
font-weight:700;
color:${color};
">

${status}

</div>

<div style="
display:grid;
grid-template-columns:1fr 1fr;
gap:16px;
margin-top:26px;
">

<div style="
background:#1f2937;
border-radius:18px;
padding:18px;
text-align:center;
">

<div style="
font-size:30px;
margin-bottom:8px;
">
❤️
</div>

<div style="
font-size:28px;
font-weight:700;
">

${recovery}

</div>

<div style="
margin-top:4px;
font-size:12px;
color:#9ca3af;
letter-spacing:1px;
">

Recovery

</div>

</div>

<div style="
background:#1f2937;
border-radius:18px;
padding:18px;
text-align:center;
">

<div style="
font-size:30px;
margin-bottom:8px;
">
⚡
</div>

<div style="
font-size:22px;
font-weight:700;
">

${fatigue}

</div>

<div style="
margin-top:4px;
font-size:12px;
color:#9ca3af;
letter-spacing:1px;
">

Fatigue

</div>

</div>

<div style="
background:#1f2937;
border-radius:18px;
padding:18px;
text-align:center;
">

<div style="
font-size:30px;
margin-bottom:8px;
">
💪
</div>

<div style="
font-size:22px;
font-weight:700;
text-transform:capitalize;
">

${fitness}

</div>

<div style="
margin-top:4px;
font-size:12px;
color:#9ca3af;
letter-spacing:1px;
">

Fitness

</div>

</div>

<div style="
background:#1f2937;
border-radius:18px;
padding:18px;
text-align:center;
">

<div style="
font-size:30px;
margin-bottom:8px;
">
🎯
</div>

<div style="
font-size:28px;
font-weight:700;
color:${color};
">

${score}

</div>

<div style="
margin-top:4px;
font-size:12px;
color:#9ca3af;
letter-spacing:1px;
">

Coach Score

</div>

</div>

</div>
<div style="
margin-top:26px;
background:#1f2937;
border-radius:20px;
padding:20px;
">

<div style="
font-size:13px;
letter-spacing:2px;
color:#9ca3af;
margin-bottom:16px;
">

TODAY'S TRAINING

</div>

<div style="
font-size:26px;
font-weight:700;
margin-bottom:18px;
">

🚴 ${workout}

</div>

<div style="
display:grid;
grid-template-columns:1fr 1fr;
gap:14px;
">

<div style="
background:#111827;
padding:14px;
border-radius:14px;
text-align:center;
">

<div style="font-size:26px;">⏱</div>

<div style="
font-size:22px;
font-weight:700;
margin-top:6px;
">

${duration}

</div>

<div style="
font-size:12px;
color:#9ca3af;
">

Minutes

</div>

</div>

<div style="
background:#111827;
padding:14px;
border-radius:14px;
text-align:center;
">

<div style="font-size:26px;">🎯</div>

<div style="
font-size:22px;
font-weight:700;
margin-top:6px;
">

${tss}

</div>

<div style="
font-size:12px;
color:#9ca3af;
">

Target TSS

</div>

</div>

<div style="
background:#111827;
padding:14px;
border-radius:14px;
text-align:center;
">

<div style="font-size:26px;">📍</div>

<div style="
font-size:18px;
font-weight:700;
margin-top:6px;
">

${zone}

</div>

<div style="
font-size:12px;
color:#9ca3af;
">

Training Zone

</div>

</div>

<div style="
background:#111827;
padding:14px;
border-radius:14px;
text-align:center;
">

<div style="font-size:26px;">🧠</div>

<div style="
font-size:18px;
font-weight:700;
margin-top:6px;
color:${color};
">

${status}

</div>

<div style="
font-size:12px;
color:#9ca3af;
">

Coach AI

</div>

</div>

</div>

</div>
`;

  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return {
      rows: 5,
      columns: 6,
      min_rows: 4,
      min_columns: 4,
    };
  }

}

customElements.define("coach-ai-card", CoachAICard);

window.customCards = window.customCards || [];

window.customCards.push({
  type: "coach-ai-card",
  name: "Coach AI",
  description: "Professional dashboard for Coach AI",
  preview: true,
});