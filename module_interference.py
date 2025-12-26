import json
import os
from groq import Groq
import traceback
from dotenv import load_dotenv
import importlib
import re

# Load environment variables from .env if present
load_dotenv()


def generate_description(text: str, title: str, max_length: int = 400) -> str:
    """
    Generate a meaningful description from content following a heading.
    
    Extracts 1-2 sentences that best describe the section.
    
    Args:
        text: Full text content around the heading
        title: The heading/module title
        max_length: Maximum description length
        
    Returns:
        str: Generated description
    """
    # Remove HTML tags
    clean = re.sub(r"<.*?>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    
    # Split into sentences (period, exclamation, question mark)
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    
    if not sentences:
        return title
    
    # Build description with 1-2 sentences, respecting length limit
    description_parts = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Skip very short fragments or sentences that are just the title
        if len(sentence) < 10 or sentence.lower() == title.lower():
            continue
        
        # Check if adding this sentence would exceed limit
        if current_length + len(sentence) + 1 <= max_length:
            description_parts.append(sentence)
            current_length += len(sentence) + 1
            
            # Stop after 2 sentences
            if len(description_parts) >= 2:
                break
    
    if not description_parts:
        # Fallback: take first meaningful snippet
        words = clean.split()[:20]  # First 20 words
        return " ".join(words)
    
    return " ".join(description_parts)


def local_extract(text: str, max_modules: int = 10):
    """Improved local extraction: parse headings, divs, aria-labels, and lists.
    Returns a list of modules matching the AI output format."""
    import re, bisect

    headings = []
    # HTML headings h1-h6
    for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", text, flags=re.I | re.S):
        level = int(m.group(1))
        title = re.sub(r"<.*?>", "", m.group(2)).strip()
        if title and len(title) > 2:
            headings.append((m.start(), level, title))

    # Markdown headings
    for m in re.finditer(r"^(#{1,6})\s*(.+)$", text, flags=re.M):
        level = len(m.group(1))
        title = m.group(2).strip()
        if title and len(title) > 2:
            headings.append((m.start(), level, title))

    # Extract aria-label attributes (common in modern SPAs like Instagram Help)
    for m in re.finditer(r'aria-label=["\']([^"\']{4,100})["\']', text, flags=re.I):
        title = m.group(1).strip()
        if title and not any(h[2] == title for h in headings):
            headings.append((m.start(), 3, title))

    # Extract text from divs with role="heading"
    for m in re.finditer(r'<div[^>]*role=["\']heading["\'][^>]*>(.*?)</div>', text, flags=re.I | re.S):
        title = re.sub(r"<.*?>", "", m.group(1)).strip()
        if title and len(title) > 2:
            headings.append((m.start(), 2, title))

    headings.sort(key=lambda x: x[0])
    # Deduplicate by title (keep first occurrence)
    seen = {}
    unique_headings = []
    for pos, lvl, title in headings:
        if title not in seen:
            seen[title] = True
            unique_headings.append((pos, lvl, title))
    headings = unique_headings

    # If no explicit headings found, fallback to chunking text
    if not headings:
        chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
        modules = []
        for ch in chunks[:max_modules]:
            lines = ch.splitlines()
            title = lines[0][:80]
            desc = " ".join(lines[1:3]) if len(lines) > 1 else ch[:200]
            modules.append({"module": title, "Description": desc.strip(), "Submodules": {}})
        return modules

    # determine top level: if only h1 and many h2, use h2 as top; else use smallest heading
    levels = [lvl for _, lvl, _ in headings]
    h1_count = sum(1 for lvl in levels if lvl == 1)
    h2_count = sum(1 for lvl in levels if lvl == 2)
    
    if h1_count == 1 and h2_count > 2:
        # Likely a page title + section structure; use h2 as modules
        top_level = 2
    else:
        # Otherwise use the most common or smallest level
        top_level = 1 if 1 in levels else (2 if 2 in levels else min(levels))

    # collect top-level modules and their section ranges
    top_positions = []
    modules = []
    for idx, (pos, lvl, title) in enumerate(headings):
        if lvl == top_level:
            start = pos
            # end is next top-level heading start or end of text
            next_top = next((p for p, l, t in headings[idx+1:] if l == top_level), None)
            end = next_top if next_top is not None else len(text)
            section = text[start:end]
            
            # Generate intelligent description from section content
            description = generate_description(section, title, max_length=400)
            
            modules.append({"module": title, "Description": description, "Submodules": {}})
            top_positions.append(start)

    # attach submodules within each top-level section
    for pos, lvl, title in headings:
        if lvl > top_level:
            # find which top-level section this belongs to
            idx = bisect.bisect_right(top_positions, pos) - 1
            if idx < 0 or idx >= len(modules):
                continue
            # determine snippet for this subheading until next heading
            next_pos = next((p for p, l, t in headings if p > pos), None)
            end = next_pos if next_pos is not None else len(text)
            snippet = text[pos:end]
            clean = re.sub(r"<.*?>", "", snippet)
            clean = re.sub(r"\s+", " ", clean).strip()
            # prefer paragraph after heading
            parts = re.split(r"\n\s*\n", clean)
            sub_desc = parts[1].strip() if len(parts) > 1 else (parts[0][:300] if parts else "")
            # if list items exist under this heading, capture them as submodules
            list_items = re.findall(r"<li[^>]*>(.*?)</li>", snippet, flags=re.I | re.S)
            if list_items:
                # make each list item a submodule entry
                for li in list_items:
                    li_text = re.sub(r"<.*?>", "", li).strip()
                    if li_text and len(li_text) > 2:
                        modules[idx]["Submodules"][li_text] = ""
            else:
                modules[idx]["Submodules"][title] = sub_desc

    # If some modules have no submodules, try extracting <li> lists in their section
    for module_idx, (pos, lvl, title) in enumerate([(p, l, t) for p, l, t in headings if l == top_level]):
        sec_start = pos
        # Find next top-level heading position after this one
        all_top_level_positions = [p for p, l, t in headings if l == top_level]
        current_idx_in_toplevel = all_top_level_positions.index(pos)
        next_top = all_top_level_positions[current_idx_in_toplevel + 1] if current_idx_in_toplevel + 1 < len(all_top_level_positions) else None
        sec_end = next_top if next_top is not None else len(text)
        section = text[sec_start:sec_end]
        items = re.findall(r"<li[^>]*>(.*?)</li>", section, flags=re.I | re.S)
        if items and len(modules[module_idx]["Submodules"]) == 0:
            for li in items:
                li_text = re.sub(r"<.*?>", "", li).strip()
                if li_text and len(li_text) > 2:
                    modules[module_idx]["Submodules"][li_text] = ""

    return modules[:max_modules]

def infer_modules(text: str):
    prompt = f"""You are a technical documentation analyzer. Extract ALL modules, classes, and features from the documentation text.

For each module found, provide:
1. Module name (clear and concise)
2. Detailed description (2-3 sentences)
3. All submodules/classes/features within that module

Return ONLY valid JSON ARRAY. Include AS MANY modules as you find. Minimum 5 modules.

Format:
[
  {{
    "module": "Module name",
    "Description": "Detailed description of what this module does",
    "Submodules": {{
      "submodule_1": "What submodule_1 does",
      "submodule_2": "What submodule_2 does",
      "submodule_3": "What submodule_3 does"
    }}
  }}
]

DOCUMENTATION TEXT:
{text[:8000]}
"""

    try:
        # Prefer OpenAI if API key present
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                    openai_mod = importlib.import_module("openai")
                    openai_model = os.getenv("OPENAI_MODEL", "gpt-4")
                    print("Using OpenAI model:", openai_model)
                    messages = [{"role": "user", "content": prompt}]
                    # Support new openai>=1.0.0 client and fallback to old API
                    OpenAIClient = getattr(openai_mod, "OpenAI", None)
                    if OpenAIClient is not None:
                        client = OpenAIClient(api_key=openai_key)
                        resp = client.chat.completions.create(
                            model=openai_model,
                            messages=messages,
                            temperature=0.7,
                        )
                        # response shapes are similar
                        try:
                            content = resp.choices[0].message.content
                        except Exception:
                            content = resp["choices"][0]["message"]["content"]
                        successful_model = f"openai:{openai_model}"
                        print(f"OpenAI call succeeded: {successful_model}")
                    else:
                        # old API
                        openai_mod.api_key = openai_key
                        resp = openai_mod.ChatCompletion.create(
                            model=openai_model,
                            messages=messages,
                            temperature=0.7,
                        )
                        content = resp["choices"][0]["message"]["content"]
                        successful_model = f"openai:{openai_model}"
                        print(f"OpenAI (legacy) call succeeded: {successful_model}")
            except Exception as e:
                err_msg = str(e)
                print(f"OpenAI call failed: {err_msg}")
                print(traceback.format_exc())
                # Fall back to local extraction
                return local_extract(text)
            # proceed to parsing below
        else:
            # Initialize Groq client (uses GROQ_API_KEY environment variable)
            api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key:
                # No AI keys configured — use local fallback
                print("No Groq API key found; using local fallback extractor.")
                return local_extract(text)
            client = Groq(api_key=api_key)
        
        # Allow overriding model via env var; otherwise try a small fallback list
        groq_model = os.getenv("GROQ_MODEL")
        if groq_model:
            models_to_try = [groq_model]
        else:
            # Candidate models to try (order = preferred -> fallback)
            models_to_try = [
                "llama-3.1-70b-stable",
                "llama-3.1-13b-stable",
                "llama-2.1-13b-stable",
            ]

        content = None
        successful_model = None
        for model in models_to_try:
            try:
                print(f"Trying Groq model: {model}")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                content = response.choices[0].message.content
                successful_model = model
                print(f"Groq model succeeded: {model}")
                break
            except Exception as e:
                err_msg = str(e)
                print(f"Model {model} failed: {err_msg}")
                # If model was decommissioned, try next candidate
                if "decommissioned" in err_msg or "model_decommissioned" in err_msg:
                    continue
                # For other errors, fall back to local extractor
                print(traceback.format_exc())
                return local_extract(text)

        if not successful_model:
            # Try OpenAI fallback if available
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                        openai_mod = importlib.import_module("openai")
                        openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                        print("Groq models failed — trying OpenAI model:", openai_model)
                        messages = [{"role": "user", "content": prompt}]
                        OpenAIClient = getattr(openai_mod, "OpenAI", None)
                        if OpenAIClient is not None:
                            client = OpenAIClient(api_key=openai_key)
                            resp = client.chat.completions.create(
                                model=openai_model,
                                messages=messages,
                                temperature=0.7,
                            )
                            try:
                                content = resp.choices[0].message.content
                            except Exception:
                                content = resp["choices"][0]["message"]["content"]
                            successful_model = f"openai:{openai_model}"
                        else:
                            openai_mod.api_key = openai_key
                            resp = openai_mod.ChatCompletion.create(
                                model=openai_model,
                                messages=messages,
                                temperature=0.7,
                            )
                            content = resp["choices"][0]["message"]["content"]
                            successful_model = f"openai:{openai_model}"
                except Exception as e:
                    err_msg = str(e)
                    print(f"OpenAI fallback failed: {err_msg}")
                    print(traceback.format_exc())
                    return local_extract(text)
            else:
                # None of the Groq models worked and no OpenAI key — use local extractor
                print("Groq models failed and no OpenAI key set; using local fallback.")
                return local_extract(text)
    except Exception as e:
        print(f"❌ Error preparing Groq request: {str(e)}")
        print(traceback.format_exc())
        return local_extract(text)

    try:
        # Extract JSON from response
        import re
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(content)
    except:
        # fallback so Streamlit never crashes
        return [
            {
                "module": "Parsing Failed",
                "Description": "Could not parse AI response: " + content[:200],
                "Submodules": {}
            }
        ]
