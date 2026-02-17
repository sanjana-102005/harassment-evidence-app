def get_india_laws(detected_types):
    laws = []

    # Base cyber sections (common)
    laws.append(("IT Act 2000 - Section 66E", "Violation of privacy (private images/videos)."))
    laws.append(("IT Act 2000 - Section 67", "Publishing/transmitting obscene material online."))
    laws.append(("IT Act 2000 - Section 67A", "Publishing sexually explicit content online."))

    if "Threat / Intimidation" in detected_types:
        laws.append(("IPC 503", "Criminal intimidation."))
        laws.append(("IPC 506", "Punishment for criminal intimidation."))
        laws.append(("IPC 507", "Criminal intimidation by anonymous communication."))

    if "Blackmail / Sextortion" in detected_types:
        laws.append(("IPC 384", "Extortion."))
        laws.append(("IPC 385", "Putting a person in fear to commit extortion."))

    if "Stalking / Repeated Contact" in detected_types:
        laws.append(("IPC 354D", "Stalking (applies to women)."))

    if "Sexual Harassment / Physical Touching" in detected_types:
        laws.append(("IPC 354", "Assault/criminal force to woman with intent to outrage modesty."))
        laws.append(("IPC 354A", "Sexual harassment."))
        laws.append(("IPC 509", "Word/gesture intended to insult modesty of a woman."))
        laws.append(("POSH Act 2013", "Workplace sexual harassment complaint via Internal Committee (IC)."))

    if "Online Sexual Harassment / Obscene Content" in detected_types:
        laws.append(("IPC 509", "Insulting modesty of a woman."))
        laws.append(("IT Act 67", "Obscene content online."))

    if "Hate-based Harassment" in detected_types:
        laws.append(("IPC 153A", "Promoting enmity between groups."))
        laws.append(("IPC 295A", "Deliberate acts intended to outrage religious feelings."))

    if "Workplace Harassment" in detected_types:
        laws.append(("POSH Act 2013", "Workplace harassment complaint via Internal Committee (IC)."))

    if "General Verbal Abuse" in detected_types:
        laws.append(("IPC 504", "Intentional insult to provoke breach of peace."))

    # remove duplicates
    uniq = []
    seen = set()
    for sec, desc in laws:
        if sec not in seen:
            uniq.append((sec, desc))
            seen.add(sec)

    return uniq