def generate_summary(text: str) -> str:
    """
    Generate emergency medical summary from patient data.
    Replace this with actual AI model integration later.
    """
    if not text:
        return "No medical data available for summary."
    
    # Simple rule-based summary for demo
    # In production, replace with HuggingFace/OpenAI API call
    
    summary_parts = []
    
    # Extract key information
    if "Blood Group:" in text:
        blood_group = text.split("Blood Group:")[1].split("\n")[0].strip()
        summary_parts.append(f"Blood type: {blood_group}")
    
    if "Allergies:" in text:
        allergies = text.split("Allergies:")[1].split("\n")[0].strip()
        if allergies.lower() not in ["none", "none known", "no known allergies"]:
            summary_parts.append(f"Allergies: {allergies}")
        else:
            summary_parts.append("No known allergies")
    
    if "Current Medications:" in text:
        meds = text.split("Current Medications:")[1].split("\n")[0].strip()
        if meds and meds.lower() not in ["none", "no current medications"]:
            summary_parts.append(f"Current medications: {meds}")
    
    if "Conditions:" in text:
        conditions = text.split("Conditions:")[1].split("\n")[0].strip()
        if conditions and conditions.lower() not in ["none", "no conditions"]:
            summary_parts.append(f"Medical conditions: {conditions}")
    
    # Add recent abnormal findings
    abnormal_indicators = ["high", "low", "elevated", "abnormal", "critical"]
    lines = text.lower().split('\n')
    for line in lines:
        if any(indicator in line for indicator in abnormal_indicators):
            if "blood glucose" in line or "sugar" in line:
                summary_parts.append("Note: Recent blood glucose levels may require attention")
            elif "cholesterol" in line or "ldl" in line:
                summary_parts.append("Note: Cholesterol levels elevated")
            elif "pressure" in line:
                summary_parts.append("Note: Blood pressure reading noted")
    
    if not summary_parts:
        return "Standard health profile. No critical issues detected."
    
    return " | ".join(summary_parts) + " | Seek professional medical advice for emergency care."