// Text on the site, outside the machine cards. Edit with tools/site-editor.html.
// HTML is allowed (links, <b>, <code>). In ramDspLine, {mk2} and {mk1} are filled in per machine.
window.SITE_TEXT = {
  "tagline": "Custom USR machines for the Elektron Machinedrum on the <a href=\"https://github.com/jmamma/MDX\">MDX X.20 firmware</a>, focused on sample mangling and effects processing.",
  "ask": "Let me know how you get on with these and if you have any suggestions!",
  "discussion": "Discussion: <a href=\"https://www.elektronauts.com/t/custom-usr-machines-for-x-20/257233\">Custom USR Machines for X.20</a> on Elektronauts, and the <b class=\"nowrap\">mdx-usr-machines</b> thread on the <a href=\"https://discord.gg/H2wVG6eH2\">MDX Discord</a>.",
  "installTitle": "How to install",
  "installSteps": [
    "Update your MD to <a href=\"https://github.com/jmamma/MDX\">MDX X.20</a>. Back up your data first! ",
    "On the MD: <b>FUNC+GLOBAL → FILE → MACHINE MGR</b>, pick an empty slot, choose <b>RECV</b> (it shows WAITING…).",
    "Send the <code>.syx</code> with SysEx Librarian or your SysEx app of choice. Several files can go at once as they fill empty slots.",
    "The new machines appear under <b>KIT → EDIT</b>."
  ],
  "installNote": "",
  "disclaimer": "<b>Disclaimer:</b> Again, be sure to back up your Machinedrum (sounds, kits, patterns) before installing anything, firmware updates included. These machines are tested and run smoothly on a UW+ MKII, but you download and use them at your own risk; they come as they are, with no guarantee. Made with LLM help for the coding; not affiliated with MDX development.",
  "licence": "<b>License:</b> The USR machines (source code and .syx files) are free software under the <a href=\"https://www.gnu.org/licenses/gpl-3.0.html\">GNU General Public License v3.0 or later</a>: use them in your music (commercial releases included), share and modify them, as long as anything you pass on stays under the same license with its source. The demo samples are not covered. Source on <a href=\"https://github.com/murdenihcam/murdenihcam-usr-machines\">my GitHub</a>.",
  "footer": "<a href=\"https://github.com/murdenihcam/murdenihcam-usr-machines\">murdenihcam USR machines GitHub repo</a>",
  "samplersTitle": "Samplers",
  "samplersSub": "Playback and manipulation of samples in the UW ROM and/or E12 banks.",
  "ramTitle": "RAM machines",
  "ramSub": "Record and playback live audio into RAM in one machine. nUW world soundz",
  "nfxTitle": "NFX effects",
  "nfxSub": "Effects that process the tracks before them.",
  "tracksCaption": "The max number of tracks of this machine can run in one kit, estimated from its certified DSP cycles. ",
  "ramTracksCaption": "RAM machines use one of the MD's RAM slots, so a pattern can play at most 4 of them on an MKII (R1–R4) and 2 on an MKI (R1–R2), or a mix of 4 RAM machines.",
  "ramDspLine": ""
};
