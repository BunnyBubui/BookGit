from config.Config import Colors

def GetStatus(val):
    if val > 35.0: 
        return f"{Colors.RED}⚠️ Severe!{Colors.RESET}"
    if val > 25.0: 
        return f"{Colors.YELLOW}🟡 Moderate{Colors.RESET}"
    return f"{Colors.GREEN}✅ Normal{Colors.RESET}"