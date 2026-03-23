import ast
import sys
from pathlib import Path

def delete_comments(input_file: str, output_file: str) -> None:
    input_path: Path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f'输入文件不存在: {input_file}')
    source: str = input_path.read_text(encoding='utf-8')
    try:
        tree: ast.Module = ast.parse(source)
    except SyntaxError as e:
        raise SyntaxError(f'解析失败: {e}')
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        tree.body.pop(0)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
        if isinstance(node, ast.AnnAssign):
            if hasattr(node, 'simple'):
                node.simple = 1
    try:
        new_source: str = ast.unparse(tree)
    except AttributeError:
        raise RuntimeError('Python 3.9+ 需要ast.unparse支持')
    output_path: Path = Path(output_file)
    output_path.write_text(new_source, encoding='utf-8')

def main() -> int:
    if len(sys.argv) < 2:
        print('用法: python comment_deleter.py <输入文件> [输出文件]')
        print('示例: python comment_deleter.py input.py output.py')
        return 1
    input_file: str = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file: str = sys.argv[2]
    else:
        input_path: Path = Path(input_file)
        output_file = str(input_path.parent / f'{input_path.stem}_clean{input_path.suffix}')
    try:
        delete_comments(input_file, output_file)
        print(f'已删除注释: {input_file} -> {output_file}')
        return 0
    except FileNotFoundError as e:
        print(f'错误: {e}')
        return 1
    except SyntaxError as e:
        print(f'错误: {e}')
        return 1
    except Exception as e:
        print(f'错误: {e}')
        return 1
if __name__ == '__main__':
    sys.exit(main())