#!/bin/bash
# =====================================================
# 🦊 fix_firefox_audio.sh
# Automatically restarts Firefox if audio stops working
# Works on Debian / Ubuntu / PipeWire / PulseAudio
# =====================================================

# Adjust this if you use a different user
USER_NAME="$USER"

# Check every 30 seconds
CHECK_INTERVAL=30

echo "🔊 Firefox Audio Watchdog started..."
echo "Monitoring Firefox sound state every ${CHECK_INTERVAL}s"

while true; do
    # 1️⃣ Check if Firefox is running
    if pgrep -u "$USER_NAME" firefox > /dev/null; then
        
        # 2️⃣ Check if Firefox is playing or registered in audio
        # Using pactl (works for PulseAudio and PipeWire)
        if ! pactl list sink-inputs | grep -q "application.name = \"Firefox\""; then
            echo "⚠️  No active Firefox audio stream detected. Restarting Firefox..."
            pkill firefox
            sleep 2
            nohup firefox > /dev/null 2>&1 &
            echo "✅ Firefox restarted at $(date)"
            sleep 10  # Give it time to reinitialize
        fi
    fi

    sleep "$CHECK_INTERVAL"
done
