#!/usr/bin/env bash
# ==========================================================
# 🧩 HelixNet System Info & Diagnostics (v2.5)
# ==========================================================
#  Purpose: Friendly OS + hardware + Docker + dependency report
#  Author: Angel 🧩 + Sherlock
# ----------------------------------------------------------
set -Eeuo pipefail
trap 'echo "🚨 CRASH ALERT! The Builder (🤴) tripped on line $LINENO in script $0!"' ERR
SECONDS=0

# --- Try loading environment ---
[[ -f ".env" ]] && source ".env"

# --- Colors -------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;36m'; CYAN='\033[0;39m'; NC='\033[0m'
BOLD="\033[1m"; RESET="\033[0m"

# --- Utility header printer ---------------------------------
print_header() {
    printf "\n${CYAN}════════════════════════════════════════════════════════════════${NC}\n"
    printf "${CYAN}💡 %s${NC}\n" "$1"
    printf "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"
}

# ==========================================================
# 🧱 SECTION 1 – GENERAL SYSTEM INFO
# ==========================================================
report_system_info() {
    print_header "🖥️  GENERAL SYSTEM INFORMATION"
    printf "${YELLOW}Hostname:${NC}        %s\n" "$(hostname)"
    printf "${YELLOW}User:${NC}            %s\n" "$(whoami)"
    printf "${YELLOW}Uptime:${NC}          %s\n" "$(uptime -p)"
    printf "${YELLOW}OS / Distro:${NC}     %s\n" "$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')"
    printf "${YELLOW}Kernel:${NC}          %s\n" "$(uname -r)"
    printf "${YELLOW}Architecture:${NC}    %s\n" "$(uname -m)"
}

# ==========================================================
# 🧠 SECTION 2 – CPU / PROCESSOR INFO
# ==========================================================
report_cpu_info() {
    print_header "🧠 CPU INFORMATION"
    local MODEL CORES MHZ
    MODEL=$(lscpu | awk -F: '/Model name/{print $2}' | sed 's/^ *//')
    CORES=$(nproc)
    MHZ=$(lscpu | awk -F: '/CPU max MHz/{print $2}' | sed 's/^ *//')
    printf "${YELLOW}Model:${NC}             %s\n" "$MODEL"
    printf "${YELLOW}Cores:${NC}             %s\n" "$CORES"
    [[ -n "$MHZ" ]] && printf "${YELLOW}Max Freq:${NC}         %.2f GHz\n" "$(echo "$MHZ / 1000" | bc -l)"
    printf "${YELLOW}Load Avg (1m):${NC}    %s\n" "$(awk '{print $1}' /proc/loadavg)"
}

# ==========================================================
# 💾 SECTION 3 – MEMORY
# ==========================================================
report_memory_info() {
    print_header "💾 MEMORY (RAM & SWAP)"
    free -h | awk 'NR==1{print $0} NR>1{print $0}' | column -t
}

# ==========================================================
# 🗄️ SECTION 4 – DISK
# ==========================================================
report_disk_info() {
    print_header "🗄️  DISK SPACE"
    df -hT --total | grep -E '^Filesystem|/dev/' | column -t
}

# ==========================================================
# 🌐 SECTION 5 – NETWORK
# ==========================================================
report_network_info() {
    print_header "🌐 NETWORK INTERFACES"
    ip -br a | awk -v Y="$YELLOW" -v N="$NC" '
        $1 != "lo" {
            printf "%s%-10s%s  %-6s  %s\n", Y, $1, N, $2, $3
        }'
    echo
    printf "${YELLOW}Default Route:${NC} "; ip route show default 2>/dev/null | head -n1 || echo "n/a"
    printf "${YELLOW}DNS Servers:${NC}  "; grep "nameserver" /etc/resolv.conf | awk '{print $2}' | xargs
}

# ==========================================================
# 🐳 SECTION 6 – DOCKER ENVIRONMENT
# ==========================================================
report_docker_info() {
    print_header "🐳 DOCKER ENVIRONMENT"
    if ! command -v docker &>/dev/null; then
        echo "${RED}Docker not installed.${NC}"
        return
    fi
    docker version --format '{{.Server.Version}}' >/dev/null 2>&1 && {
        printf "${YELLOW}Version:${NC}        %s\n" "$(docker version --format '{{.Server.Version}}')"
        printf "${YELLOW}Containers:${NC}     %s running\n" "$(docker ps -q | wc -l)"
        printf "${YELLOW}Images:${NC}         %s\n" "$(docker images -q | wc -l)"
        printf "${YELLOW}Networks:${NC}       %s\n" "$(docker network ls -q | wc -l)"
    } || echo "${RED}Docker not responding.${NC}"
}

# ==========================================================
# 🔍 SECTION 7 – REQUIRED TOOL CHECKS
# ==========================================================
report_tool_checks() {
    print_header "🧰 TOOLCHAIN CHECK"
    local tools=(git curl jq awk sed bc docker gum)
    for t in "${tools[@]}"; do
        if command -v "$t" >/dev/null 2>&1; then
            printf "%b %-10s${NC} detected\n" "${GREEN}✔" "$t"
        else
            printf "%b %-10s${NC} missing (install recommended)\n" "${RED}✖" "$t"
        fi
    done
}

# ==========================================================
# 💡 SECTION 8 – EDUCATIONAL LINKS
# ==========================================================
report_links() {
    print_header "💡 LEARN & TROUBLESHOOT"
    cat <<EOF
🧩 Useful Links:
  - Docker Basics: https://docs.docker.com/get-started/
  - Ollama Setup:  https://ollama.ai/download
  - HelixNet Docs: (coming soon)
  - Check ports:   sudo ss -tulnp | grep -E '8000|11434|5432'
  - Monitor:       htop  or  docker stats
EOF
}

# ==========================================================
# MAIN ENTRY
# ==========================================================
main() {
    
    echo -e "${GREEN}=============================================================================${NC}"
    echo -e "${GREEN} 💦️  HELIXNET SYSTEM DIAGNOSTIC REPORT ⏱️  $(date '+%Y-%m-%d %H:%M:%S') ${NC}"
    echo -e "${GREEN}=================> ./scripts/modules/tools/helix-checks.sh <=================${NC}"

    report_system_info
    report_cpu_info
    report_memory_info
    report_disk_info
    report_network_info
    report_docker_info
    report_tool_checks
    report_links

    echo -e "\n${GREEN}✅ REPORT COMPLETE in ${SECONDS}s${NC}"
    echo -e "${BLUE}Returning to Control Center...${NC}"

    # if command -v gum &>/dev/null; then
    #     gum spin --spinner pulse --title "⌛ Reviewing results... advancing in a few seconds" -- sleep 20
    # else
     for i in $(seq 1 20); do printf "."; sleep 1; done; echo
    # fi
}

main
