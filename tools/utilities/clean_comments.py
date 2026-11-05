import ast
import io
import py_compile
import tokenize
from pathlib import Path

def strip_code(source: str) -> str:
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    
    lines = source.splitlines(keepends=True)
    
    # Identify comments
    comment_ranges = []
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            # Keep encoding cookie if first or second line, otherwise strip
            if tok.start[0] <= 2 and "coding" in tok.string:
                continue
            comment_ranges.append((tok.start[0] - 1, tok.start[1], tok.end[0] - 1, tok.end[1]))
            
    # Remove comments from lines (from end of file to start)
    for s_line, s_col, e_line, e_col in reversed(comment_ranges):
        line = lines[s_line]
        # If the line only contains the comment (and whitespace), remove the whole line
        if line[:s_col].strip() == "":
            lines[s_line] = ""
        else:
            lines[s_line] = line[:s_col].rstrip() + "\n"

    new_source = "".join(lines)
    
    # Identify module and function docstrings using ast
    try:
        tree = ast.parse(new_source)
        doc_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)):
                    doc_nodes.append(node.body[0])
                    
        # Sort docstrings descending by lineno
        doc_nodes.sort(key=lambda n: n.lineno, reverse=True)
        split_lines = new_source.splitlines(keepends=True)
        for d in doc_nodes:
            s_idx = d.lineno - 1
            e_idx = d.end_lineno
            # If docstring is inside a block, we can replace it with pass if the block would become empty
            # But here docstrings are followed by actual code, so we just clear those lines
            for i in range(s_idx, e_idx):
                split_lines[i] = ""
        new_source = "".join(split_lines)
    except Exception as e:
        print(f"AST parse error: {e}")

    # Clean up excessive blank lines
    final_lines = []
    blank_count = 0
    for line in new_source.splitlines(keepends=True):
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                final_lines.append("\n")
        else:
            blank_count = 0
            final_lines.append(line)

    result = "".join(final_lines).lstrip()
    return result

def process_file(file_path: Path):
    print(f"Processing: {file_path}")
    source = file_path.read_text(encoding="utf-8")
    cleaned = strip_code(source)
    
    # Temporary test compile
    temp_test = file_path.with_suffix(".tmp_test.py")
    temp_test.write_text(cleaned, encoding="utf-8")
    try:
        py_compile.compile(str(temp_test), doraise=True)
        temp_test.unlink()
        file_path.write_text(cleaned, encoding="utf-8")
        print(f"  OK: Cleaned and verified {file_path.name}")
    except Exception as err:
        if temp_test.exists():
            temp_test.unlink()
        print(f"  ERROR compiling {file_path.name}: {err}")

def main():
    target_files = [
        Path("tools/reinsertion/patch_exe.py"),
        Path("tools/reinsertion/patch_fax.py"),
        Path("tools/reinsertion/patch_ranking.py"),
        Path("tools/reinsertion/patch_stg0101.py"),
        Path("tools/reinsertion/patch_stg7000.py"),
        Path("tools/reinsertion/patch_stg7500.py"),
        Path("tools/reinsertion/batch_repack.py"),
        Path("tools/extraction/batch_extract.py"),
        Path("tools/extraction/ghm_lz.py"),
        Path("tools/utilities/gdl_tool.py"),
        Path("tools/utilities/patch_strimag.py"),
        Path("tools/release/build_release_package.py"),
        Path("release/No_More_Heroes_2_Traducao_PTBR_Beta/patch_exe.py"),
    ]
    
    for f in target_files:
        if f.exists():
            process_file(f)

if __name__ == "__main__":
    main()
