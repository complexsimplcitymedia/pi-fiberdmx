# Fiber Laser DMX Controller

## Quick Setup (Fresh Raspberry Pi)

**Step 1: Open Terminal on your Pi**

**Step 2: Copy and paste these 4 lines:**
```bash
git clone https://github.com/complexsimplcitymedia/fiber-laser-dmx.git
cd fiber-laser-dmx
chmod +x setup.sh
./setup.sh
```

**Step 3: Wait for it to finish (takes about 10-15 minutes)**

**Step 4: Reboot when prompted:**
```bash
sudo reboot
```

That's it. The system will start automatically after reboot.

---

## Access the UI

- **On the Pi itself:** Opens automatically in kiosk mode
- **From another device:** http://laser-dmx.local or http://[Pi-IP-Address]:8080

---

# Fiber Channel Control System

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/42778fa6d6544beca449703dbed7d8d8)](https://app.codacy.com?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

### Environment

* **Python Environments:** No `python3` environments
* **Active Environment:** `miniconda3`

---

## Channel Description

| Channel # | Fiber | Strand Color | Morse Strand | Morse Strand # |
| --------- | ----- | ------------ | ------------ | -------------- |
| 1         | A     | Red          | D            | 1              |
| 2         | A     | Red          | D            | 2              |
| 3         | A     | Red          | D            | 3              |
| 4         | A     | Green        | G            | 4              |
| 5         | A     | Green        | G            | 5              |
| 6         | A     | Green        | G            | 6              |
| 7         | A     | Infrared     | U            | 1              |
| 8         | A     | Infrared     | U            | 2              |
| 9         | A     | Infrared     | U            | 3              |
| 10        | A     | Infrared     | U            | 4              |
| 11        | A     | Infrared     | U            | 5              |
| 12        | A     | Infrared     | U            | 6              |

---

## Function Buttons

| Function                      | Description                                                                      |
| ----------------------------- | -------------------------------------------------------------------------------- |
| **Flash All Visible (1-6)**   | Activates flashing for all visible light fibers (Channels 1-6).                  |
| **Flash All Infrared (7-12)** | Activates flashing for all infrared fibers (Channels 7-12).                      |
| **Mode Switch**               | Formerly "Flash All." Toggles between operating modes or pattern configurations. |

---

## Channel Controls (Manual VFL Testing)

| Channel        | Description                                                                |
| -------------- | -------------------------------------------------------------------------- |
| **Channel #1** | Turns Channel #1 ON (100%) or OFF (100%) independently for VFL #1 testing. |
| **Channel #2** | Turns Channel #2 ON (100%) or OFF (100%) independently for VFL #2 testing. |
| **Channel #3** | Turns Channel #3 ON (100%) or OFF (100%) independently for VFL #3 testing. |
| **Channel #4** | Turns Channel #4 ON (100%) or OFF (100%) independently for VFL #4 testing. |
| **Channel #5** | Turns Channel #5 ON (100%) or OFF (100%) independently for VFL #5 testing. |
| **Channel #6** | Turns Channel #6 ON (100%) or OFF (100%) independently for VFL #6 testing. |

---

## Remote App Integration

| Remote Button             | Function                                                                                            |
| ------------------------- | --------------------------------------------------------------------------------------------------- |
| **OLS Button**            | Toggles Optical Light Source 100% ON/OFF.                                                           |
| **OTDR Button**           | Toggles Optical Time-Domain Reflectometer 100% ON/OFF.                                              |
| **Remote Viewing Button** | Enables remote monitoring of channel status and diagnostics.                                        |
| **Wi-Fi Options Button**  | Opens wireless configuration settings for device pairing, SSID selection, and remote control setup. |

---

## Other Test / Control Buttons

| Button            | Function                                                      |
| ----------------- | ------------------------------------------------------------- |
| **Test Channels** | Runs diagnostic checks across all active fibers.              |
| **Pattern Stop**  | Stops any ongoing flashing sequence or pattern.               |
| **Shutdown**      | Safely disables all channels and terminates system processes. |

---

## Notes

* Flash patterns correspond to **Morse code designations** per strand group (`D`, `G`, `U`).
* Visible light channels: **1-6**
* Infrared channels: **7-12**
* Remote features and Wi-Fi options should synchronize with local button states to prevent conflicts.
