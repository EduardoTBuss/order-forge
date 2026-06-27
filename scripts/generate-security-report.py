import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def load_json_file(filepath: Path) -> dict | list | None:
    """Load a JSON file, returning None if it doesn't exist or is invalid."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {filepath}: {e}", file=sys.stderr)
        return None


def load_mapping(mapping_path: Path) -> dict:
    """Load the OWASP/SANS mapping configuration."""
    mapping = load_json_file(mapping_path)
    if not mapping:
        print(f"Error: Could not load mapping file: {mapping_path}", file=sys.stderr)
        sys.exit(1)
    return mapping


def extract_cwe_from_text(text: str) -> list[str]:
    """Extract CWE identifiers from text."""
    pattern = r"CWE-(\d+)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [f"CWE-{m}" for m in matches]


def map_cwe_to_owasp(cwe: str, mapping: dict) -> str | None:
    """Map a CWE identifier to an OWASP Top 10 category."""
    owasp_mapping = mapping.get("owasp_top_10", {})
    for owasp_id, data in owasp_mapping.items():
        if cwe in data.get("cwes", []):
            return owasp_id
    return None


def map_cwe_to_sans25(cwe: str, mapping: dict) -> dict | None:
    """Map a CWE identifier to SANS Top 25 if it's in the list."""
    sans_mapping = mapping.get("sans_cwe_top_25", {})
    return sans_mapping.get(cwe)


def parse_semgrep_results(filepath: Path, mapping: dict) -> list[dict]:
    """Parse Semgrep JSON results and extract findings."""
    data = load_json_file(filepath)
    if not data:
        return []

    findings = []
    results = data.get("results", [])

    for result in results:
        rule_id = result.get("check_id", "unknown")
        message = result.get("extra", {}).get("message", "")
        severity = result.get("extra", {}).get("severity", "INFO")
        filepath_str = result.get("path", "unknown")
        line_start = result.get("start", {}).get("line", 0)
        line_end = result.get("end", {}).get("line", 0)

        # Extract CWE from metadata or message
        metadata = result.get("extra", {}).get("metadata", {})
        cwes = metadata.get("cwe", [])
        if isinstance(cwes, str):
            cwes = [cwes]

        # Also try to extract from message
        cwes.extend(extract_cwe_from_text(message))
        cwes.extend(extract_cwe_from_text(rule_id))

        # Get OWASP category from metadata
        owasp_categories = metadata.get("owasp", [])
        if isinstance(owasp_categories, str):
            owasp_categories = [owasp_categories]

        # Map CWEs to OWASP if not already provided
        for cwe in cwes:
            owasp = map_cwe_to_owasp(cwe, mapping)
            if owasp and owasp not in owasp_categories:
                owasp_categories.append(owasp)

        finding = {
            "source": "semgrep",
            "rule_id": rule_id,
            "message": message,
            "severity": severity.upper(),
            "file": filepath_str,
            "line_start": line_start,
            "line_end": line_end,
            "cwes": list(set(cwes)),
            "owasp_categories": list(set(owasp_categories)),
            "references": metadata.get("references", []),
        }
        findings.append(finding)

    return findings


def parse_bandit_results(filepath: Path, mapping: dict) -> list[dict]:
    """Parse Bandit JSON results and extract findings."""
    data = load_json_file(filepath)
    if not data:
        return []

    findings = []
    results = data.get("results", [])
    bandit_mapping = mapping.get("bandit_test_mappings", {})

    for result in results:
        test_id = result.get("test_id", "unknown")
        test_name = result.get("test_name", "unknown")
        issue_text = result.get("issue_text", "")
        severity = result.get("issue_severity", "LOW")
        confidence = result.get("issue_confidence", "LOW")
        filepath_str = result.get("filename", "unknown")
        line_number = result.get("line_number", 0)

        # Get CWE and OWASP mapping
        test_info = bandit_mapping.get(test_id, {})
        cwe = test_info.get("cwe")
        owasp = test_info.get("owasp")

        cwes = [cwe] if cwe else []
        owasp_categories = [owasp] if owasp else []

        finding = {
            "source": "bandit",
            "rule_id": f"{test_id}:{test_name}",
            "message": issue_text,
            "severity": severity.upper(),
            "confidence": confidence.upper(),
            "file": filepath_str,
            "line_start": line_number,
            "line_end": line_number,
            "cwes": cwes,
            "owasp_categories": owasp_categories,
            "references": [
                f"https://bandit.readthedocs.io/en/latest/plugins/{test_id.lower()}_{test_name}.html"
            ],
        }
        findings.append(finding)

    return findings


def parse_pip_audit_results(filepath: Path, mapping: dict) -> list[dict]:
    """Parse pip-audit JSON results."""
    data = load_json_file(filepath)
    if not data:
        return []

    findings = []
    vulnerabilities = data if isinstance(data, list) else data.get("vulnerabilities", [])

    for vuln in vulnerabilities:
        # Handle both formats
        if isinstance(vuln, dict):
            package = vuln.get("name", vuln.get("package", "unknown"))
            version = vuln.get("version", "unknown")
            vuln_id = vuln.get("id", vuln.get("vulnerability_id", "unknown"))
            description = vuln.get("description", vuln.get("advisory", ""))
            fix_versions = vuln.get("fix_versions", vuln.get("fixed_in", []))

            finding = {
                "source": "pip-audit",
                "rule_id": vuln_id,
                "message": f"{package}@{version}: {description}",
                "severity": "HIGH",  # pip-audit doesn't always provide severity
                "package": package,
                "version": version,
                "fix_versions": fix_versions,
                "cwes": extract_cwe_from_text(description),
                "owasp_categories": ["A06:2021"],  # Vulnerable Components
                "references": [f"https://pypi.org/project/{package}/"],
            }
            findings.append(finding)

    return findings


def parse_pnpm_audit_results(
    filepath: Path, source_name: str, mapping: dict
) -> list[dict]:
    """Parse pnpm audit JSON results."""
    data = load_json_file(filepath)
    if not data:
        return []

    findings = []
    vulnerabilities = data.get("vulnerabilities", {})

    for pkg_name, vuln_data in vulnerabilities.items():
        severity = vuln_data.get("severity", "low")
        via = vuln_data.get("via", [])

        for v in via:
            if isinstance(v, dict):
                finding = {
                    "source": source_name,
                    "rule_id": str(v.get("source", "unknown")),
                    "message": f"{pkg_name}: {v.get('title', 'Unknown vulnerability')}",
                    "severity": severity.upper(),
                    "package": pkg_name,
                    "version": vuln_data.get("range", "unknown"),
                    "cwes": extract_cwe_from_text(str(v.get("cwe", []))),
                    "owasp_categories": ["A06:2021"],  # Vulnerable Components
                    "references": [v.get("url", "")],
                }
                findings.append(finding)

    return findings


def parse_njsscan_results(filepath: Path, source_name: str, mapping: dict) -> list[dict]:
    """Parse njsscan JSON results."""
    data = load_json_file(filepath)
    if not data:
        return []

    findings = []
    # njsscan output structure: {"nodejs": {...}, "templates": {...}, ...}
    # Each category contains rules with findings

    for category, rules in data.items():
        if not isinstance(rules, dict):
            continue

        for rule_id, rule_data in rules.items():
            if not isinstance(rule_data, dict):
                continue

            metadata = rule_data.get("metadata", {})
            severity = metadata.get("severity", "INFO")
            description = metadata.get("description", "")
            cwe = metadata.get("cwe", "")
            owasp = metadata.get("owasp", "")

            # Extract CWEs
            cwes = extract_cwe_from_text(cwe) if cwe else []

            # Map OWASP references
            owasp_categories = []
            if owasp:
                # njsscan uses format like "A1:2017" or "A03:2021"
                owasp_match = re.search(r"A\d{1,2}:\d{4}", owasp)
                if owasp_match:
                    owasp_categories.append(owasp_match.group())

            # Process each file with findings
            files = rule_data.get("files", [])
            for file_info in files:
                file_path = file_info.get("file_path", "unknown")
                match_lines = file_info.get("match_lines", [0, 0])
                match_string = file_info.get("match_string", "")

                finding = {
                    "source": source_name,
                    "rule_id": rule_id,
                    "message": f"{description} - {match_string[:100]}"
                    if match_string
                    else description,
                    "severity": severity.upper(),
                    "file": file_path,
                    "line_start": match_lines[0] if match_lines else 0,
                    "line_end": match_lines[1]
                    if len(match_lines) > 1
                    else match_lines[0],
                    "cwes": cwes,
                    "owasp_categories": owasp_categories,
                    "references": [metadata.get("ref", "")],
                }
                findings.append(finding)

    return findings


def parse_trufflehog_results(filepath: Path, mapping: dict) -> list[dict]:
    """Parse TruffleHog JSON results (newline-delimited JSON format)."""
    if not filepath.exists():
        return []

    findings = []

    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
            if not content:
                return []

            # TruffleHog outputs newline-delimited JSON
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    result = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # TruffleHog result structure
                detector_name = result.get(
                    "DetectorName", result.get("detectorName", "unknown")
                )
                detector_type = result.get(
                    "DetectorType", result.get("detectorType", "")
                )
                verified = result.get("Verified", result.get("verified", False))

                # Source metadata
                source_metadata = result.get(
                    "SourceMetadata", result.get("sourceMetadata", {})
                )
                data = source_metadata.get("Data", source_metadata.get("data", {}))

                # Try different source types (filesystem, git, etc.)
                filepath_str = "unknown"
                line_num = 0
                commit = ""

                if "Filesystem" in data:
                    fs_data = data["Filesystem"]
                    filepath_str = fs_data.get("file", "unknown")
                    line_num = fs_data.get("line", 0)
                elif "Git" in data:
                    git_data = data["Git"]
                    filepath_str = git_data.get("file", "unknown")
                    line_num = git_data.get("line", 0)
                    commit = git_data.get("commit", "")

                # Determine severity based on verification status
                severity = "CRITICAL" if verified else "HIGH"

                finding = {
                    "source": "trufflehog",
                    "rule_id": f"{detector_name}"
                    + (f" ({detector_type})" if detector_type else ""),
                    "message": f"{'Verified ' if verified else 'Potential '}{detector_name} secret detected in {filepath_str}",
                    "severity": severity,
                    "file": filepath_str,
                    "line_start": line_num,
                    "line_end": line_num,
                    "commit": commit,
                    "verified": verified,
                    "cwes": ["CWE-798"],  # Hardcoded credentials
                    "owasp_categories": ["A07:2021"],  # Authentication Failures
                    "references": [
                        "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/"
                    ],
                }
                findings.append(finding)

    except IOError as e:
        print(f"Warning: Could not load {filepath}: {e}", file=sys.stderr)
        return []

    return findings


def parse_trivy_results(filepath: Path, mapping: dict) -> list[dict]:
    """Parse Trivy JSON results."""
    data = load_json_file(filepath)
    if not data:
        return []

    findings = []
    results = data.get("Results", [])

    for result in results:
        target = result.get("Target", "unknown")
        vulnerabilities = result.get("Vulnerabilities", [])

        for vuln in vulnerabilities or []:
            vuln_id = vuln.get("VulnerabilityID", "unknown")
            pkg_name = vuln.get("PkgName", "unknown")
            installed_version = vuln.get("InstalledVersion", "unknown")
            fixed_version = vuln.get("FixedVersion", "")
            severity = vuln.get("Severity", "UNKNOWN")
            description = vuln.get("Description", "")
            cwes = vuln.get("CweIDs", [])

            finding = {
                "source": "trivy",
                "rule_id": vuln_id,
                "message": f"{pkg_name}@{installed_version}: {description[:200]}",
                "severity": severity.upper(),
                "package": pkg_name,
                "version": installed_version,
                "fix_version": fixed_version,
                "target": target,
                "cwes": cwes,
                "owasp_categories": ["A06:2021"],  # Vulnerable Components
                "references": vuln.get("References", [])[:3],
            }
            findings.append(finding)

    return findings


def categorize_findings(findings: list[dict], mapping: dict) -> dict:
    """Categorize all findings by OWASP Top 10 and SANS Top 25."""
    owasp_findings = defaultdict(list)
    sans_findings = defaultdict(list)
    uncategorized = []

    owasp_info = mapping.get("owasp_top_10", {})
    sans_info = mapping.get("sans_cwe_top_25", {})

    for finding in findings:
        categorized = False

        # Categorize by OWASP
        for owasp_cat in finding.get("owasp_categories", []):
            if owasp_cat in owasp_info:
                owasp_findings[owasp_cat].append(finding)
                categorized = True

        # Categorize by SANS/CWE
        for cwe in finding.get("cwes", []):
            if cwe in sans_info:
                sans_findings[cwe].append(finding)
                categorized = True

        # Also map CWEs to OWASP if not already done
        for cwe in finding.get("cwes", []):
            owasp = map_cwe_to_owasp(cwe, mapping)
            if owasp and owasp not in finding.get("owasp_categories", []):
                owasp_findings[owasp].append(finding)
                categorized = True

        if not categorized:
            uncategorized.append(finding)

    return {
        "owasp": dict(owasp_findings),
        "sans": dict(sans_findings),
        "uncategorized": uncategorized,
    }


def count_by_severity(findings: list[dict]) -> dict[str, int]:
    """Count findings by severity level."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0, "UNKNOWN": 0}
    for finding in findings:
        severity = finding.get("severity", "UNKNOWN").upper()
        if severity in counts:
            counts[severity] += 1
        else:
            counts["UNKNOWN"] += 1
    return counts


def generate_owasp_json(categorized: dict, mapping: dict) -> dict:
    """Generate OWASP Top 10 findings JSON."""
    owasp_info = mapping.get("owasp_top_10", {})
    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "framework": "OWASP Top 10 2021",
        "categories": {},
    }

    for owasp_id in sorted(owasp_info.keys()):
        info = owasp_info[owasp_id]
        findings = categorized["owasp"].get(owasp_id, [])

        result["categories"][owasp_id] = {
            "name": info["name"],
            "description": info["description"],
            "finding_count": len(findings),
            "severity_breakdown": count_by_severity(findings),
            "findings": findings,
        }

    return result


def generate_sans_json(categorized: dict, mapping: dict) -> dict:
    """Generate SANS/CWE Top 25 findings JSON."""
    sans_info = mapping.get("sans_cwe_top_25", {})
    result = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "framework": "CWE Top 25 2023",
        "categories": {},
    }

    for cwe_id, info in sorted(sans_info.items(), key=lambda x: x[1]["rank"]):
        findings = categorized["sans"].get(cwe_id, [])

        result["categories"][cwe_id] = {
            "rank": info["rank"],
            "name": info["name"],
            "description": info["description"],
            "finding_count": len(findings),
            "severity_breakdown": count_by_severity(findings),
            "findings": findings,
        }

    return result


def generate_markdown_report(
    all_findings: list[dict],
    categorized: dict,
    mapping: dict,
    dep_findings: list[dict],
    secret_findings: list[dict],
) -> str:
    """Generate a comprehensive Markdown security report."""
    owasp_info = mapping.get("owasp_top_10", {})
    sans_info = mapping.get("sans_cwe_top_25", {})

    total_severity = count_by_severity(all_findings)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# Security Audit Report",
        "",
        f"**Generated:** {timestamp}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"**Total Findings:** {len(all_findings)}",
        "",
        "### Findings by Severity",
        "",
        "| Severity | Count |",
        "|----------|-------|",
    ]

    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        count = total_severity.get(sev, 0)
        emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "INFO": "🔵",
        }.get(sev, "⚪")
        lines.append(f"| {emoji} {sev} | {count} |")

    lines.extend(
        [
            "",
            "### OWASP Top 10 Coverage",
            "",
            "| Category | Name | Findings |",
            "|----------|------|----------|",
        ]
    )

    for owasp_id in sorted(owasp_info.keys()):
        info = owasp_info[owasp_id]
        count = len(categorized["owasp"].get(owasp_id, []))
        status = "✅" if count == 0 else f"⚠️ {count}"
        lines.append(f"| {owasp_id} | {info['name']} | {status} |")

    lines.extend(
        [
            "",
            "### SANS/CWE Top 25 Coverage",
            "",
            "| Rank | CWE | Name | Findings |",
            "|------|-----|------|----------|",
        ]
    )

    for cwe_id, info in sorted(sans_info.items(), key=lambda x: x[1]["rank"]):
        count = len(categorized["sans"].get(cwe_id, []))
        status = "✅" if count == 0 else f"⚠️ {count}"
        lines.append(f"| {info['rank']} | {cwe_id} | {info['name']} | {status} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## OWASP Top 10 Findings",
            "",
        ]
    )

    for owasp_id in sorted(owasp_info.keys()):
        info = owasp_info[owasp_id]
        findings = categorized["owasp"].get(owasp_id, [])

        lines.extend(
            [
                f"### {owasp_id} - {info['name']}",
                "",
                f"> {info['description']}",
                "",
            ]
        )

        if not findings:
            lines.extend(["✅ No findings in this category.", ""])
        else:
            lines.extend(
                [
                    f"**{len(findings)} finding(s)**",
                    "",
                ]
            )

            for i, finding in enumerate(findings[:10], 1):  # Limit to 10 per category
                lines.extend(
                    [
                        f"#### {i}. [{finding['severity']}] {finding['rule_id']}",
                        "",
                        f"- **Source:** {finding['source']}",
                        f"- **Message:** {finding['message'][:200]}",
                    ]
                )
                if finding.get("file"):
                    lines.append(
                        f"- **Location:** `{finding['file']}:{finding.get('line_start', '?')}`"
                    )
                if finding.get("cwes"):
                    lines.append(f"- **CWEs:** {', '.join(finding['cwes'])}")
                lines.append("")

            if len(findings) > 10:
                lines.append(f"*... and {len(findings) - 10} more findings*")
                lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## SANS/CWE Top 25 Findings",
            "",
        ]
    )

    for cwe_id, info in sorted(sans_info.items(), key=lambda x: x[1]["rank"]):
        findings = categorized["sans"].get(cwe_id, [])

        if findings:
            lines.extend(
                [
                    f"### {cwe_id} (Rank #{info['rank']}) - {info['name']}",
                    "",
                    f"> {info['description']}",
                    "",
                    f"**{len(findings)} finding(s)**",
                    "",
                ]
            )

            for i, finding in enumerate(findings[:5], 1):
                lines.extend(
                    [
                        f"- **[{finding['severity']}]** {finding['rule_id']}: {finding['message'][:150]}",
                    ]
                )
            lines.append("")

            if len(findings) > 5:
                lines.append(f"*... and {len(findings) - 5} more findings*")
                lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Dependency Vulnerabilities",
            "",
        ]
    )

    if dep_findings:
        lines.extend(
            [
                f"**{len(dep_findings)} vulnerable dependencies found**",
                "",
                "| Package | Version | Vulnerability | Severity |",
                "|---------|---------|---------------|----------|",
            ]
        )

        for finding in dep_findings[:20]:
            pkg = finding.get("package", "unknown")
            ver = finding.get("version", "?")
            vuln_id = finding.get("rule_id", "unknown")
            sev = finding.get("severity", "UNKNOWN")
            lines.append(f"| {pkg} | {ver} | {vuln_id} | {sev} |")

        if len(dep_findings) > 20:
            lines.append("")
            lines.append(f"*... and {len(dep_findings) - 20} more vulnerabilities*")
    else:
        lines.append("✅ No dependency vulnerabilities found.")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Secret Detection Results",
            "",
        ]
    )

    if secret_findings:
        lines.extend(
            [
                f"⚠️ **{len(secret_findings)} potential secret(s) detected**",
                "",
            ]
        )

        for finding in secret_findings[:10]:
            lines.extend(
                [
                    f"- **{finding['rule_id']}** in `{finding.get('file', 'unknown')}`",
                ]
            )

        if len(secret_findings) > 10:
            lines.append("")
            lines.append(f"*... and {len(secret_findings) - 10} more secrets*")
    else:
        lines.append("✅ No secrets detected.")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Remediation Recommendations",
            "",
            "### Priority Actions",
            "",
            "1. **Critical/High Severity:** Address all critical and high severity findings immediately",
            "2. **Secrets:** Rotate any detected secrets and remove from codebase",
            "3. **Dependencies:** Update vulnerable packages to patched versions",
            "4. **Injection Flaws:** Review and fix all SQL/Command/Code injection vulnerabilities",
            "",
            "### Resources",
            "",
            "- [OWASP Top 10](https://owasp.org/Top10/)",
            "- [CWE Top 25](https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html)",
            "- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)",
            "",
            "---",
            "",
            "*Report generated by Security Audit Workflow*",
        ]
    )

    return "\n".join(lines)


def generate_html_report(markdown_content: str) -> str:
    """Generate an HTML report from markdown content."""
    # Simple HTML wrapper with basic styling
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Audit Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #1a1a1a; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; margin-top: 40px; }}
        h3 {{ color: #34495e; }}
        h4 {{ color: #7f8c8d; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        tr:hover {{ background: #f5f5f5; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background: #f9f9f9;
            color: #666;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eee;
            margin: 30px 0;
        }}
        .severity-critical {{ color: #c0392b; font-weight: bold; }}
        .severity-high {{ color: #e67e22; font-weight: bold; }}
        .severity-medium {{ color: #f1c40f; }}
        .severity-low {{ color: #27ae60; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <pre style="white-space: pre-wrap; font-family: inherit;">{markdown_content}</pre>
    </div>
</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate security audit report")
    parser.add_argument(
        "--input-dir", required=True, help="Directory containing scan results"
    )
    parser.add_argument("--output-dir", required=True, help="Directory to write reports")
    parser.add_argument(
        "--mapping", required=True, help="Path to OWASP/SANS mapping JSON"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    mapping_path = Path(args.mapping)

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading OWASP/SANS mapping...")
    mapping = load_mapping(mapping_path)

    print("Parsing scan results...")
    all_findings = []

    # Parse Semgrep results
    semgrep_path = input_dir / "semgrep-results.json"
    semgrep_findings = parse_semgrep_results(semgrep_path, mapping)
    print(f"  - Semgrep: {len(semgrep_findings)} findings")
    all_findings.extend(semgrep_findings)

    # Parse Bandit results
    bandit_path = input_dir / "bandit-results.json"
    bandit_findings = parse_bandit_results(bandit_path, mapping)
    print(f"  - Bandit: {len(bandit_findings)} findings")
    all_findings.extend(bandit_findings)

    # Parse njsscan results (frontend)
    njsscan_frontend_path = input_dir / "njsscan-frontend-results.json"
    njsscan_frontend_findings = parse_njsscan_results(
        njsscan_frontend_path, "njsscan-frontend", mapping
    )
    print(f"  - njsscan (frontend): {len(njsscan_frontend_findings)} findings")
    all_findings.extend(njsscan_frontend_findings)

    # Parse njsscan results (orchestrator)
    njsscan_orchestrator_path = input_dir / "njsscan-orchestrator-results.json"
    njsscan_orchestrator_findings = parse_njsscan_results(
        njsscan_orchestrator_path, "njsscan-orchestrator", mapping
    )
    print(f"  - njsscan (orchestrator): {len(njsscan_orchestrator_findings)} findings")
    all_findings.extend(njsscan_orchestrator_findings)

    # Parse pip-audit results
    pip_audit_path = input_dir / "pip-audit-results.json"
    pip_findings = parse_pip_audit_results(pip_audit_path, mapping)
    print(f"  - pip-audit: {len(pip_findings)} findings")

    # Parse pnpm audit results
    pnpm_frontend_path = input_dir / "pnpm-audit-frontend.json"
    pnpm_frontend_findings = parse_pnpm_audit_results(
        pnpm_frontend_path, "pnpm-audit-frontend", mapping
    )
    print(f"  - pnpm-audit (frontend): {len(pnpm_frontend_findings)} findings")

    pnpm_orchestrator_path = input_dir / "pnpm-audit-orchestrator.json"
    pnpm_orchestrator_findings = parse_pnpm_audit_results(
        pnpm_orchestrator_path, "pnpm-audit-orchestrator", mapping
    )
    print(f"  - pnpm-audit (orchestrator): {len(pnpm_orchestrator_findings)} findings")

    # Parse Trivy results
    trivy_path = input_dir / "trivy-fs-results.json"
    trivy_findings = parse_trivy_results(trivy_path, mapping)
    print(f"  - Trivy: {len(trivy_findings)} findings")

    # Combine dependency findings
    dep_findings = (
        pip_findings
        + pnpm_frontend_findings
        + pnpm_orchestrator_findings
        + trivy_findings
    )
    all_findings.extend(dep_findings)

    # Parse TruffleHog results
    trufflehog_path = input_dir / "trufflehog-results.json"
    secret_findings = parse_trufflehog_results(trufflehog_path, mapping)
    print(f"  - TruffleHog: {len(secret_findings)} findings")
    all_findings.extend(secret_findings)

    print(f"\nTotal findings: {len(all_findings)}")

    print("Categorizing findings...")
    categorized = categorize_findings(all_findings, mapping)
    print(
        f"  - OWASP categories with findings: {len([k for k, v in categorized['owasp'].items() if v])}"
    )
    print(
        f"  - SANS/CWE categories with findings: {len([k for k, v in categorized['sans'].items() if v])}"
    )
    print(f"  - Uncategorized findings: {len(categorized['uncategorized'])}")

    print("Generating reports...")

    # Generate OWASP findings JSON
    owasp_json = generate_owasp_json(categorized, mapping)
    owasp_path = output_dir / "owasp-findings.json"
    with open(owasp_path, "w") as f:
        json.dump(owasp_json, f, indent=2, default=str)
    print(f"  - Written: {owasp_path}")

    # Generate SANS findings JSON
    sans_json = generate_sans_json(categorized, mapping)
    sans_path = output_dir / "sans25-findings.json"
    with open(sans_path, "w") as f:
        json.dump(sans_json, f, indent=2, default=str)
    print(f"  - Written: {sans_path}")

    # Generate Markdown report
    md_report = generate_markdown_report(
        all_findings, categorized, mapping, dep_findings, secret_findings
    )
    md_path = output_dir / "security-audit-report.md"
    with open(md_path, "w") as f:
        f.write(md_report)
    print(f"  - Written: {md_path}")

    # Generate HTML report
    html_report = generate_html_report(md_report)
    html_path = output_dir / "security-audit-report.html"
    with open(html_path, "w") as f:
        f.write(html_report)
    print(f"  - Written: {html_path}")

    print("\nSecurity report generation complete!")


if __name__ == "__main__":
    main()
