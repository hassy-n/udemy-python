from typing import Any
import streamlit as st

st.set_page_config(page_title="Python Mission Quest", page_icon="PY", layout="wide")

# ユーザーの回答コードを安全寄りに実行するため、使ってよい組み込み関数だけを限定する。
SAFE_BUILTINS = {
    "print": print, "len": len, "str": str, "int": int, "float": float, "bool": bool,
    "range": range, "list": list, "dict": dict, "set": set, "tuple": tuple, "sum": sum,
    "min": min, "max": max, "abs": abs, "all": all, "any": any, "sorted": sorted,
    "enumerate": enumerate, "zip": zip, "round": round, "reversed": reversed
}


class ColMock:
    # st.columns() の戻り値を簡易的に再現するためのモック。
    def __init__(self, p: "StMock") -> None:
        self.p = p
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def __getattr__(self, n: str):
        return getattr(self.p, n)


class StMock:
    # Streamlit の各部品が「呼ばれたかどうか」を記録するためのモック。
    def __init__(self) -> None:
        self.calls: set[str] = set()
    def _c(self, n: str):
        self.calls.add(n)
    def text_input(self, *a, **k): self._c("text_input"); return ""
    def number_input(self, *a, **k): self._c("number_input"); return 0
    def button(self, *a, **k): self._c("button"); return False
    def write(self, *a, **k): self._c("write")
    def metric(self, *a, **k): self._c("metric")
    def selectbox(self, *a, **k): self._c("selectbox"); return ""
    def checkbox(self, *a, **k): self._c("checkbox"); return False
    def radio(self, *a, **k): self._c("radio"); return ""
    def slider(self, *a, **k): self._c("slider"); return 0
    def dataframe(self, *a, **k): self._c("dataframe")
    def line_chart(self, *a, **k): self._c("line_chart")
    def progress(self, *a, **k): self._c("progress")
    def success(self, *a, **k): self._c("success")
    def warning(self, *a, **k): self._c("warning")
    def columns(self, n: int): self._c("columns"); return [ColMock(self) for _ in range(n)]


def build_missions() -> list[dict[str, Any]]:
    # 100個のミッション定義をまとめて作る。
    # ここで各問題のタイトル、説明、判定に使う条件を持たせている。
    m: list[dict[str, Any]] = []
    # enumerate(..., 1) は「1から始まる連番」を作る書き方。
    # ここでは Mission 1, Mission 2 ... の番号付けに使っている。
    for i, item in enumerate([
        ("user_name", "Taro"), ("lesson_count", 3), ("score_total", 150), ("amount", 4800),
        ("is_active", True), ("team_members", ["A", "B", "C"]), ("priorities", ("high", "mid", "low")),
        ("profile", {"name": "Taro", "dept": "Sales"}), ("unique_ids", {101, 102, 103}), ("weekly_hours", 38)
    ], 1):
        var, exp = item
        m.append({"id": f"m{i}", "title": f"Mission {i}: 基礎",
                  "description": "値を正しく作る", "instruction": f"`{var}` を期待値で定義してください。",
                  "hint": "代入文を使います。", "reward": "基礎完了", "type": "value", "var": var, "exp": exp})
    for i, item in enumerate([
        ("normalized_name", "Taro"), ("email_domain", "example.com"), ("first_three", [10, 20, 30]),
        ("last_item", "c"), ("numbers_sorted", [1, 2, 5, 9]), ("message", "PYTHON"),
        ("joined_tags", "todo-urgent-client"), ("name_length", 6), ("high_scores", [88, 92]), ("doubled", [2, 4, 6, 8])
    ], 11):
        var, exp = item
        m.append({"id": f"m{i}", "title": f"Mission {i}: 文字列/リスト",
                  "description": "加工して期待値へ", "instruction": f"`{var}` を期待値で定義してください。",
                  "hint": "メソッド/内包表記を使えます。", "reward": "加工スキル向上", "type": "value", "var": var, "exp": exp})

    # 関数問題は「関数名」と「テスト用の入出力例」をセットで持つ。
    # 例: ((0.8,), "pass") は「0.8 を渡したら pass を返す」という意味。
    cond_defs = [
        ("judge_attendance", "0.8以上ならpass", [((0.8,), "pass"), ((0.79,), "retry")]),
        ("check_budget", "cost<=limitでok", [((1000, 1200), "ok"), ((1300, 1200), "over")]),
        ("shipping_fee", "5000以上無料", [((5000,), 0), ((4999,), 500)]),
        ("is_overtime", "8時間超でTrue", [((9,), True), ((8,), False)]),
        ("member_rank", "3段階ランク", [((120,), "gold"), ((70,), "silver"), ((20,), "bronze")]),
        ("is_even", "偶数判定", [((4,), True), ((7,), False)]),
        ("is_business_day", "土日除外", [(("mon",), True), (("sun",), False)]),
        ("status_label", "done/todo", [((True,), "done"), ((False,), "todo")]),
        ("has_text", "空白除去で判定", [((" abc ",), True), (("   ",), False)]),
        ("stock_status", "在庫3段階", [((0,), "out"), ((3,), "low"), ((8,), "ok")]),
    ]
    for i, d in enumerate(cond_defs, 21):
        fn, rule, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: 条件分岐", "description": rule,
                  "instruction": f"`{fn}` 関数を作ってください。", "hint": "if/elif/else を使います。",
                  "reward": "条件分岐スキル向上", "type": "fn", "fn": fn,
                  "tests": [{"args": a, "out": o} for a, o in tests]})

    # ここから先は、for 文で繰り返し処理を練習する設問群。
    loop_defs = [
        ("sum_positive", [(([1, -2, 3, 4],), 8), (([-1, -5],), 0)]),
        ("count_done", [(([True, False, True],), 2), (([False, False],), 0)]),
        ("find_max", [(([5, 1, 9, 2],), 9), (([-3, -1, -7],), -1)]),
        ("reverse_text", [(("abc",), "cba"), (("python",), "nohtyp")]),
        ("factorial", [((0,), 1), ((5,), 120)]),
        ("flatten_pairs", [(([(1, 2), (3, 4)],), [1, 2, 3, 4])]),
        ("unique_preserve_order", [(([1, 2, 1, 3, 2],), [1, 2, 3])]),
        ("running_total", [(([2, 3, 1],), [2, 5, 6])]),
        ("fizzbuzz_list", [((5,), ["1", "2", "Fizz", "4", "Buzz"])]),
        ("char_frequency", [(("aba",), {"a": 2, "b": 1})]),
    ]
    for i, d in enumerate(loop_defs, 31):
        fn, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: 反復処理", "description": "forを使った処理",
                  "instruction": f"`{fn}` 関数を作ってください。", "hint": "ループで処理します。",
                  "reward": "反復処理スキル向上", "type": "fn",
                  "fn": fn, "tests": [{"args": a, "out": o} for a, o in tests]})

    # 辞書(dict)や集合(set)は、業務データを扱うときによく使う。
    map_defs = [
        ("get_department", [(({"name": "A", "dept": "HR"},), "HR")]),
        ("merge_counts", [(({"x": 2, "y": 1}, {"y": 3, "z": 4}), {"x": 2, "y": 4, "z": 4})]),
        ("invert_mapping", [(({"a": 1, "b": 2},), {1: "a", 2: "b"})]),
        ("group_by_first_letter", [((["apple", "ant", "banana"],), {"a": ["apple", "ant"], "b": ["banana"]})]),
        ("count_status", [(([{"status": "todo"}, {"status": "done"}, {"status": "todo"}],), {"todo": 2, "done": 1})]),
        ("extract_high_priority", [(([{"name": "a", "priority": "high"}, {"name": "b", "priority": "low"}],), ["a"])]),
        ("remove_duplicates_case_insensitive", [((["Tanaka", "tanaka", "Sato"],), ["Tanaka", "Sato"])]),
        ("intersect_customers", [(({"A", "B", "C"}, {"B", "D"}), {"B"})]),
        ("update_stock", [(({"pen": 5}, "pen", -2), {"pen": 3}), (({"pen": 5}, "note", 3), {"pen": 5, "note": 3})]),
        ("top_n_sales", [(({"A": 100, "B": 300, "C": 200}, 2), [("B", 300), ("C", 200)])]),
    ]
    for i, d in enumerate(map_defs, 41):
        fn, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: 辞書/集合", "description": "構造データ処理",
                  "instruction": f"`{fn}` 関数を作ってください。", "hint": "辞書・集合を活用します。",
                  "reward": "データ構造スキル向上", "type": "fn",
                  "fn": fn, "tests": [{"args": a, "out": o} for a, o in tests]})

    # ここは「関数としてどう設計するか」を学ぶブロック。
    # 引数を受け取り、return で結果を返す流れに慣れるのが目的。
    biz_defs = [
        ("safe_divide", [((10, 2), 5.0), ((10, 0), None)]),
        ("parse_int", [(("12", 0), 12), (("x", -1), -1)]),
        ("format_report", [(("田中", 85), "田中: 85点")]),
        ("calc_tax", [((1000,), 100.0), ((2000, 0.08), 160.0)]),
        ("apply_discount", [((1000, 20), 800.0), ((500, 0), 500.0)]),
        ("make_greeting", [((["A", "B"],), ["Aさん、こんにちは", "Bさん、こんにちは"])]),
        ("filter_even", [(([1, 2, 3, 4],), [2, 4])]),
        ("map_to_dict", [((["a", "b"], [1, 2]), {"a": 1, "b": 2})]),
        ("transpose", [(([[1, 2, 3], [4, 5, 6]],), [[1, 4], [2, 5], [3, 6]])]),
        ("moving_average", [(([1, 2, 3, 4], 3), [2.0, 3.0])]),
    ]
    for i, d in enumerate(biz_defs, 51):
        fn, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: 関数設計", "description": "例外/加工/集計",
                  "instruction": f"`{fn}` 関数を作ってください。", "hint": "小さく分けて実装します。",
                  "reward": "関数設計スキル向上", "type": "fn",
                  "fn": fn, "tests": [{"args": a, "out": o} for a, o in tests]})

    # 実務寄りのデータ処理。1件ずつ見て集計する形が多い。
    algo_defs = [
        ("total_revenue", [(([{"price": 100, "qty": 2}, {"price": 50, "qty": 3}],), 350)]),
        ("average_satisfaction", [(([{"score": 4}, {"score": 5}, {"score": 3}],), 4.0), (([],), 0)]),
        ("overdue_tasks", [(([{"name": "A", "due": 3, "done": False}, {"name": "B", "due": 5, "done": True}], 4), ["A"])]),
        ("department_totals", [(([{"dept": "Sales", "amount": 100}, {"dept": "Sales", "amount": 50}, {"dept": "HR", "amount": 80}],), {"Sales": 150, "HR": 80})]),
        ("best_employee", [(([{"name": "A", "sales": 120}, {"name": "B", "sales": 150}],), "B")]),
        ("normalize_scores", [(([50, 60, 70],), [0.0, 50.0, 100.0]), (([5, 5],), [100.0, 100.0])]),
        ("monthly_summary", [(([{"month": 2, "amount": 100}, {"month": 1, "amount": 50}, {"month": 2, "amount": 20}],), [(1, 50), (2, 120)])]),
        ("detect_low_stock", [(([{"name": "pen", "stock": 3, "threshold": 5}, {"name": "note", "stock": 10, "threshold": 5}],), ["pen"])]),
        ("create_invoice_lines", [(([{"name": "A", "price": 100, "qty": 2}],), ["A x 2 = 200"])]),
        ("calc_kpi", [(({"sales": 1000, "cost": 700},), {"profit": 300, "margin": 0.3}), (({"sales": 0, "cost": 0},), {"profit": 0, "margin": 0})]),
    ]
    for i, d in enumerate(algo_defs, 61):
        fn, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: 実務データ処理", "description": "業務ロジック実装",
                  "instruction": f"`{fn}` 関数を作ってください。", "hint": "辞書/リストを正しく扱います。",
                  "reward": "実務処理スキル向上", "type": "fn",
                  "fn": fn, "tests": [{"args": a, "out": o} for a, o in tests]})

    # ここは少し難しめのアルゴリズム問題。
    # 変数をどう更新していくかを追えるようになるのが重要。
    hard_defs = [
        ("binary_search", [(([1, 3, 5, 7], 5), 2), (([1, 3, 5, 7], 4), -1)]),
        ("is_palindrome", [(("Never odd or even",), True), (("Python",), False)]),
        ("is_valid_parentheses", [(("([]{})",), True), (("([)]",), False)]),
        ("longest_word", [(("python makes web apps",), "python")]),
        ("compress_chars", [(("aaabbc",), "a3b2c1")]),
        ("expand_chars", [(("a3b2c1",), "aaabbc")]),
        ("rotate_list", [(([1, 2, 3, 4, 5], 2), [4, 5, 1, 2, 3])]),
        ("chunk_list", [(([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])]),
        ("merge_sorted", [(([1, 4, 6], [2, 3, 5]), [1, 2, 3, 4, 5, 6])]),
        ("two_sum", [(([2, 7, 11, 15], 9), (0, 1)), (([1, 2, 3], 10), None)]),
    ]
    for i, d in enumerate(hard_defs, 71):
        fn, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: アルゴリズム", "description": "問題解決力を強化",
                  "instruction": f"`{fn}` 関数を作ってください。", "hint": "小さいケースから確認します。",
                  "reward": "アルゴリズム力向上", "type": "fn",
                  "fn": fn, "tests": [{"args": a, "out": o} for a, o in tests]})

    # Streamlit 問題は「正しい値を返す」ではなく、
    # 必要なUI部品を呼び出しているかを判定する。
    ui_calls = [
        ["text_input"], ["text_input", "button"], ["text_input", "button", "write"],
        ["number_input", "metric", "button"], ["selectbox", "button", "write"],
        ["checkbox", "button", "success"], ["radio", "button", "warning"],
        ["slider", "button", "write"], ["dataframe", "line_chart"], ["columns", "metric", "progress", "button"]
    ]
    for i, calls in enumerate(ui_calls, 81):
        m.append({"id": f"m{i}", "title": f"Mission {i}: Streamlit UI",
                  "description": "UI部品を組み合わせる",
                  "instruction": "指定UI部品をすべて使うコードを書いてください。",
                  "hint": "不足部品は判定メッセージに表示されます。", "reward": "UI構築スキル向上",
                  "type": "st", "calls": calls})

    # 最後はミニアプリのロジック。
    # 小さな関数を組み合わせるとアプリ全体を作りやすくなる。
    app_defs = [
        ("add_task", [(([{"id": 1, "title": "A", "due": 3, "priority": "high", "done": False}], "B", 5, "low"), [{"id": 1, "title": "A", "due": 3, "priority": "high", "done": False}, {"id": 2, "title": "B", "due": 5, "priority": "low", "done": False}])]),
        ("complete_task", [(([{"id": 1, "done": False}, {"id": 2, "done": False}], 2), [{"id": 1, "done": False}, {"id": 2, "done": True}])]),
        ("delete_task", [(([{"id": 1}, {"id": 2}, {"id": 3}], 2), [{"id": 1}, {"id": 3}])]),
        ("filter_tasks", [(([{"id": 1, "done": True}, {"id": 2, "done": False}], "all"), [{"id": 1, "done": True}, {"id": 2, "done": False}]), (([{"id": 1, "done": True}, {"id": 2, "done": False}], "done"), [{"id": 1, "done": True}]), (([{"id": 1, "done": True}, {"id": 2, "done": False}], "todo"), [{"id": 2, "done": False}])]),
        ("sort_tasks_by_due", [(([{"id": 1, "due": 5}, {"id": 2, "due": 2}],), [{"id": 2, "due": 2}, {"id": 1, "due": 5}])]),
        ("calc_progress", [(([{"done": True}, {"done": False}, {"done": True}],), 66.66666666666666), (([],), 0)]),
        ("dashboard_metrics", [(([{"done": True}, {"done": False}, {"done": False}],), {"total": 3, "done": 1, "todo": 2})]),
        ("overdue_rate", [(([{"due": 2, "done": False}, {"due": 5, "done": False}, {"due": 1, "done": True}], 4), 50.0)]),
        ("priority_summary", [(([{"priority": "high"}, {"priority": "low"}, {"priority": "high"}],), {"high": 2, "low": 1})]),
        ("recommend_next_action", [(([{"done": True, "priority": "high"}],), "レビューを実施"), (([{"done": False, "priority": "high"}, {"done": False, "priority": "low"}],), "高優先タスクに着手"), (([{"done": False, "priority": "low"}],), "通常タスクを進行")]),
    ]
    for i, d in enumerate(app_defs, 91):
        fn, tests = d
        m.append({"id": f"m{i}", "title": f"Mission {i}: ミニアプリ実装",
                  "description": "タスク管理アプリの中核ロジック",
                  "instruction": f"`{fn}` 関数を作ってください。",
                  "hint": "入力データを壊さない実装が安全です。", "reward": "アプリ開発力向上",
                  "type": "fn", "fn": fn, "tests": [{"args": a, "out": o} for a, o in tests]})
    return m


MISSIONS = build_missions()


def init_state() -> None:
    # session_state は Streamlit の画面再描画後も値を保持する場所。
    # 普通の変数はボタンを押すたびに初期化されるが、session_state は次の描画にも残る。
    if "current" not in st.session_state:
        st.session_state.current = 0
    if "cleared" not in st.session_state:
        st.session_state.cleared = set()
    if "feedback" not in st.session_state:
        st.session_state.feedback = None


def mission_progress() -> float:
    # クリア済み件数 / 全件数 で進捗率を計算する。
    return len(st.session_state.cleared) / len(MISSIONS)


def is_cleared(i: int) -> bool:
    # 辞書の "id" を使って、そのミッションがクリア済みかを調べる。
    return MISSIONS[i]["id"] in st.session_state.cleared


def run_code(code: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    # ユーザーが入力したコードを実行し、作られた変数や関数を取り出せるようにする。
    # ns は namespace の略で、「変数や関数が入る箱」と考えると分かりやすい。
    ns: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
    if extra:
        ns.update(extra)
    exec(code, ns, ns)
    return ns


def eq(a: Any, b: Any) -> bool:
    # list / dict / float などを含んでも比較できるように、型ごとに比較方法を分ける。
    # float は 0.1 + 0.2 のように誤差が出ることがあるため、完全一致ではなく近さで比較する。
    if isinstance(b, float) and isinstance(a, (int, float)):
        return abs(float(a) - b) < 1e-9
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(eq(x, y) for x, y in zip(a, b))
    if isinstance(a, tuple) and isinstance(b, tuple):
        return len(a) == len(b) and all(eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a.keys()) == set(b.keys()) and all(eq(a[k], b[k]) for k in b)
    if isinstance(a, set) and isinstance(b, set):
        return a == b
    return a == b


def evaluate_mission(i: int, code: str) -> tuple[bool, str]:
    # ミッションの種類ごとに、回答コードが正しいかを判定する。
    # tuple[bool, str] は「成功/失敗」と「説明メッセージ」を一緒に返している。
    if not code.strip():
        return False, "コードが空です。"
    ms = MISSIONS[i]
    try:
        if ms["type"] == "value":
            ns = run_code(code)
            # value 問題では、指定された変数名が作られているかをまず確認する。
            if ms["var"] not in ns:
                return False, f"`{ms['var']}` が見つかりません。"
            if eq(ns[ms["var"]], ms["exp"]):
                return True, "値が正しいです。"
            return False, f"`{ms['var']}` の値が期待と異なります。"
        if ms["type"] == "fn":
            ns = run_code(code)
            fn = ns.get(ms["fn"])
            # callable(...) は「関数として呼び出せるか」を確かめる書き方。
            if not callable(fn):
                return False, f"`{ms['fn']}` 関数が見つかりません。"
            for t in ms["tests"]:
                # *args は、タプルの中身を関数の引数として順番に渡す書き方。
                args = t["args"] if isinstance(t["args"], tuple) else tuple(t["args"])
                out = fn(*args)
                if not eq(out, t["out"]):
                    return False, f"テスト不一致: 入力 {args} の期待値は {t['out']} です。"
            return True, "すべてのテストを通過しました。"
        if ms["type"] == "st":
            # Streamlit 問題では、本物の st の代わりにモックを渡して呼び出し回数を調べる。
            sm = StMock()
            run_code(code, {"st": sm})
            miss = [c for c in ms["calls"] if c not in sm.calls]
            if miss:
                return False, "不足している呼び出し: " + ", ".join(f"st.{x}" for x in miss)
            return True, "必要なUI部品の利用を確認しました。"
        return False, "判定対象外です。"
    except SyntaxError as e:
        return False, f"構文エラー: {e.msg} (line {e.lineno})"
    except Exception as e:
        return False, f"実行エラー: {type(e).__name__}: {e}"


def freeze_obj(v: Any) -> Any:
    if isinstance(v, list):
        return ("__list__", tuple(freeze_obj(x) for x in v))
    if isinstance(v, tuple):
        return ("__tuple__", tuple(freeze_obj(x) for x in v))
    if isinstance(v, dict):
        items = sorted((repr(k), freeze_obj(val)) for k, val in v.items())
        return ("__dict__", tuple(items))
    if isinstance(v, set):
        return ("__set__", tuple(sorted(freeze_obj(x) for x in v)))
    return v


def build_sample_solution(ms: dict[str, Any]) -> str:
    # 各ミッションの模範解答を文字列で返し、そのまま画面に表示できる形にする。
    if ms["type"] == "value":
        # repr(...) を使うと、文字列なら引用符付き、辞書なら辞書の形で表示できる。
        return f"{ms['var']} = {repr(ms['exp'])}"

    if ms["type"] == "st":
        snippets = {
            "text_input": "name = st.text_input('名前')",
            "number_input": "value = st.number_input('数値', min_value=0, value=0)",
            "button": "clicked = st.button('実行')",
            "write": "st.write('入力内容をここに表示します')",
            "metric": "st.metric('KPI', 100)",
            "selectbox": "choice = st.selectbox('選択してください', ['A', 'B'])",
            "checkbox": "agreed = st.checkbox('確認しました')",
            "radio": "option = st.radio('優先度', ['高', '中'])",
            "slider": "level = st.slider('進捗', 0, 100, 50)",
            "dataframe": "st.dataframe([{'item': 'A', 'value': 10}, {'item': 'B', 'value': 20}])",
            "line_chart": "st.line_chart([10, 20, 15, 30])",
            "progress": "st.progress(60)",
            "success": "st.success('保存しました')",
            "warning": "st.warning('入力内容を確認してください')",
            "columns": "col1, col2 = st.columns(2)",
        }
        lines = [snippets[call] for call in ms["calls"] if call in snippets]
        if "button" in ms["calls"] and "write" in ms["calls"]:
            lines.append("if clicked:\n    st.write('ボタンが押されました')")
        return "\n".join(lines)

    if ms["type"] == "fn":
        # 関数問題は、関数名ごとに読みやすい模範解答を用意している。
        answer_map = {
            "judge_attendance": "def judge_attendance(rate):\n    if rate >= 0.8:\n        return 'pass'\n    return 'retry'",
            "check_budget": "def check_budget(cost, limit):\n    if cost <= limit:\n        return 'ok'\n    return 'over'",
            "shipping_fee": "def shipping_fee(amount):\n    if amount >= 5000:\n        return 0\n    return 500",
            "is_overtime": "def is_overtime(hours):\n    return hours > 8",
            "member_rank": "def member_rank(points):\n    if points >= 100:\n        return 'gold'\n    if points >= 50:\n        return 'silver'\n    return 'bronze'",
            "is_even": "def is_even(n):\n    return n % 2 == 0",
            "is_business_day": "def is_business_day(day):\n    return day not in ['sat', 'sun']",
            "status_label": "def status_label(is_done):\n    if is_done:\n        return 'done'\n    return 'todo'",
            "has_text": "def has_text(text):\n    return len(text.strip()) > 0",
            "stock_status": "def stock_status(stock):\n    if stock == 0:\n        return 'out'\n    if stock < 5:\n        return 'low'\n    return 'ok'",
            "sum_positive": "def sum_positive(nums):\n    total = 0\n    for num in nums:\n        if num > 0:\n            total += num\n    return total",
            "count_done": "def count_done(flags):\n    count = 0\n    for flag in flags:\n        if flag:\n            count += 1\n    return count",
            "find_max": "def find_max(nums):\n    return max(nums)",
            "reverse_text": "def reverse_text(text):\n    return text[::-1]",
            "factorial": "def factorial(n):\n    result = 1\n    for value in range(1, n + 1):\n        result *= value\n    return result",
            "flatten_pairs": "def flatten_pairs(pairs):\n    result = []\n    for left, right in pairs:\n        result.append(left)\n        result.append(right)\n    return result",
            "unique_preserve_order": "def unique_preserve_order(items):\n    result = []\n    seen = set()\n    for item in items:\n        if item not in seen:\n            seen.add(item)\n            result.append(item)\n    return result",
            "running_total": "def running_total(nums):\n    total = 0\n    result = []\n    for num in nums:\n        total += num\n        result.append(total)\n    return result",
            "fizzbuzz_list": "def fizzbuzz_list(n):\n    result = []\n    for value in range(1, n + 1):\n        if value % 15 == 0:\n            result.append('FizzBuzz')\n        elif value % 3 == 0:\n            result.append('Fizz')\n        elif value % 5 == 0:\n            result.append('Buzz')\n        else:\n            result.append(str(value))\n    return result",
            "char_frequency": "def char_frequency(text):\n    result = {}\n    for ch in text:\n        result[ch] = result.get(ch, 0) + 1\n    return result",
            "get_department": "def get_department(employee):\n    return employee['dept']",
            "merge_counts": "def merge_counts(a, b):\n    result = dict(a)\n    for key, value in b.items():\n        result[key] = result.get(key, 0) + value\n    return result",
            "invert_mapping": "def invert_mapping(d):\n    return {value: key for key, value in d.items()}",
            "group_by_first_letter": "def group_by_first_letter(words):\n    result = {}\n    for word in words:\n        first = word[0]\n        result.setdefault(first, []).append(word)\n    return result",
            "count_status": "def count_status(tasks):\n    result = {}\n    for task in tasks:\n        status = task['status']\n        result[status] = result.get(status, 0) + 1\n    return result",
            "extract_high_priority": "def extract_high_priority(tasks):\n    result = []\n    for task in tasks:\n        if task['priority'] == 'high':\n            result.append(task['name'])\n    return result",
            "remove_duplicates_case_insensitive": "def remove_duplicates_case_insensitive(names):\n    result = []\n    seen = set()\n    for name in names:\n        key = name.lower()\n        if key not in seen:\n            seen.add(key)\n            result.append(name)\n    return result",
            "intersect_customers": "def intersect_customers(a, b):\n    return a & b",
            "update_stock": "def update_stock(stock, item, delta):\n    result = dict(stock)\n    result[item] = result.get(item, 0) + delta\n    return result",
            "top_n_sales": "def top_n_sales(sales_dict, n):\n    items = sorted(sales_dict.items(), key=lambda x: x[1], reverse=True)\n    return items[:n]",
            "safe_divide": "def safe_divide(a, b):\n    if b == 0:\n        return None\n    return a / b",
            "parse_int": "def parse_int(text, default):\n    try:\n        return int(text)\n    except ValueError:\n        return default",
            "format_report": "def format_report(name, score):\n    return f'{name}: {score}点'",
            "calc_tax": "def calc_tax(amount, rate=0.1):\n    return amount * rate",
            "apply_discount": "def apply_discount(price, percent):\n    return price * (1 - percent / 100)",
            "make_greeting": "def make_greeting(names):\n    result = []\n    for name in names:\n        result.append(f'{name}さん、こんにちは')\n    return result",
            "filter_even": "def filter_even(nums):\n    return [num for num in nums if num % 2 == 0]",
            "map_to_dict": "def map_to_dict(keys, values):\n    return dict(zip(keys, values))",
            "transpose": "def transpose(matrix):\n    result = []\n    for col in range(len(matrix[0])):\n        row = []\n        for line in matrix:\n            row.append(line[col])\n        result.append(row)\n    return result",
            "moving_average": "def moving_average(nums, window):\n    result = []\n    for i in range(len(nums) - window + 1):\n        part = nums[i:i + window]\n        result.append(sum(part) / window)\n    return result",
            "total_revenue": "def total_revenue(records):\n    total = 0\n    for record in records:\n        total += record['price'] * record['qty']\n    return total",
            "average_satisfaction": "def average_satisfaction(records):\n    if not records:\n        return 0\n    total = 0\n    for record in records:\n        total += record['score']\n    return total / len(records)",
            "overdue_tasks": "def overdue_tasks(tasks, today):\n    result = []\n    for task in tasks:\n        if not task['done'] and task['due'] < today:\n            result.append(task['name'])\n    return result",
            "department_totals": "def department_totals(records):\n    result = {}\n    for record in records:\n        dept = record['dept']\n        result[dept] = result.get(dept, 0) + record['amount']\n    return result",
            "best_employee": "def best_employee(records):\n    best = max(records, key=lambda x: x['sales'])\n    return best['name']",
            "normalize_scores": "def normalize_scores(scores):\n    low = min(scores)\n    high = max(scores)\n    if low == high:\n        return [100.0 for _ in scores]\n    result = []\n    for score in scores:\n        result.append((score - low) / (high - low) * 100)\n    return result",
            "monthly_summary": "def monthly_summary(records):\n    totals = {}\n    for record in records:\n        month = record['month']\n        totals[month] = totals.get(month, 0) + record['amount']\n    return sorted(totals.items())",
            "detect_low_stock": "def detect_low_stock(items):\n    result = []\n    for item in items:\n        if item['stock'] < item['threshold']:\n            result.append(item['name'])\n    return result",
            "create_invoice_lines": "def create_invoice_lines(items):\n    result = []\n    for item in items:\n        total = item['price'] * item['qty']\n        result.append(f\"{item['name']} x {item['qty']} = {total}\")\n    return result",
            "calc_kpi": "def calc_kpi(data):\n    profit = data['sales'] - data['cost']\n    margin = 0 if data['sales'] == 0 else profit / data['sales']\n    return {'profit': profit, 'margin': margin}",
            "binary_search": "def binary_search(sorted_nums, target):\n    left = 0\n    right = len(sorted_nums) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if sorted_nums[mid] == target:\n            return mid\n        if sorted_nums[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
            "is_palindrome": "def is_palindrome(text):\n    normalized = text.replace(' ', '').lower()\n    return normalized == normalized[::-1]",
            "is_valid_parentheses": "def is_valid_parentheses(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in '([{':\n            stack.append(ch)\n        else:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return len(stack) == 0",
            "longest_word": "def longest_word(sentence):\n    words = sentence.split()\n    best = words[0]\n    for word in words[1:]:\n        if len(word) > len(best):\n            best = word\n    return best",
            "compress_chars": "def compress_chars(text):\n    result = ''\n    count = 1\n    for i in range(1, len(text) + 1):\n        if i < len(text) and text[i] == text[i - 1]:\n            count += 1\n        else:\n            result += text[i - 1] + str(count)\n            count = 1\n    return result",
            "expand_chars": "def expand_chars(text):\n    result = ''\n    i = 0\n    while i < len(text):\n        ch = text[i]\n        num = text[i + 1]\n        result += ch * int(num)\n        i += 2\n    return result",
            "rotate_list": "def rotate_list(nums, k):\n    k = k % len(nums)\n    return nums[-k:] + nums[:-k]",
            "chunk_list": "def chunk_list(nums, size):\n    result = []\n    for i in range(0, len(nums), size):\n        result.append(nums[i:i + size])\n    return result",
            "merge_sorted": "def merge_sorted(a, b):\n    result = []\n    i = 0\n    j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i])\n            i += 1\n        else:\n            result.append(b[j])\n            j += 1\n    result.extend(a[i:])\n    result.extend(b[j:])\n    return result",
            "two_sum": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        need = target - num\n        if need in seen:\n            return (seen[need], i)\n        seen[num] = i\n    return None",
            "add_task": "def add_task(tasks, title, due, priority):\n    new_task = {\n        'id': len(tasks) + 1,\n        'title': title,\n        'due': due,\n        'priority': priority,\n        'done': False,\n    }\n    return tasks + [new_task]",
            "complete_task": "def complete_task(tasks, task_id):\n    result = []\n    for task in tasks:\n        updated = dict(task)\n        if updated['id'] == task_id:\n            updated['done'] = True\n        result.append(updated)\n    return result",
            "delete_task": "def delete_task(tasks, task_id):\n    return [task for task in tasks if task['id'] != task_id]",
            "filter_tasks": "def filter_tasks(tasks, status):\n    if status == 'all':\n        return tasks\n    if status == 'done':\n        return [task for task in tasks if task['done']]\n    return [task for task in tasks if not task['done']]",
            "sort_tasks_by_due": "def sort_tasks_by_due(tasks):\n    return sorted(tasks, key=lambda task: task['due'])",
            "calc_progress": "def calc_progress(tasks):\n    if not tasks:\n        return 0\n    done = 0\n    for task in tasks:\n        if task['done']:\n            done += 1\n    return done / len(tasks) * 100",
            "dashboard_metrics": "def dashboard_metrics(tasks):\n    total = len(tasks)\n    done = sum(1 for task in tasks if task['done'])\n    return {'total': total, 'done': done, 'todo': total - done}",
            "overdue_rate": "def overdue_rate(tasks, today):\n    if not tasks:\n        return 0\n    overdue = 0\n    active = 0\n    for task in tasks:\n        if not task['done']:\n            active += 1\n            if task['due'] < today:\n                overdue += 1\n    if active == 0:\n        return 0\n    return overdue / active * 100",
            "priority_summary": "def priority_summary(tasks):\n    result = {}\n    for task in tasks:\n        priority = task['priority']\n        result[priority] = result.get(priority, 0) + 1\n    return result",
            "recommend_next_action": "def recommend_next_action(tasks):\n    undone = [task for task in tasks if not task['done']]\n    if len(undone) == 0:\n        return 'レビューを実施'\n    for task in undone:\n        if task['priority'] == 'high':\n            return '高優先タスクに着手'\n    return '通常タスクを進行'",
        }
        return answer_map.get(ms["fn"], f"def {ms['fn']}(*args):\n    pass")

    return "# no sample"


def build_lesson_explanation(ms: dict[str, Any]) -> str:
    # 問題タイプに応じて「この設問で何を学ぶのか」を文章で返す。
    if ms["type"] == "value":
        return "このレッスンでは、値を変数に代入する基本と、文字列・数値・リスト・辞書などのデータ型の違いを理解してほしいです。"
    if ms["type"] == "st":
        return "このレッスンでは、Streamlit の部品を組み合わせて画面を作る基本を学んでほしいです。入力部品と表示部品をつなぐ感覚が重要です。"
    if ms["type"] == "fn":
        fn = ms["fn"]
        groups = {
            "条件分岐": {"judge_attendance", "check_budget", "shipping_fee", "is_overtime", "member_rank", "is_even", "is_business_day", "status_label", "has_text", "stock_status"},
            "反復処理": {"sum_positive", "count_done", "find_max", "reverse_text", "factorial", "flatten_pairs", "unique_preserve_order", "running_total", "fizzbuzz_list", "char_frequency"},
            "辞書と集合": {"get_department", "merge_counts", "invert_mapping", "group_by_first_letter", "count_status", "extract_high_priority", "remove_duplicates_case_insensitive", "intersect_customers", "update_stock", "top_n_sales"},
            "関数設計": {"safe_divide", "parse_int", "format_report", "calc_tax", "apply_discount", "make_greeting", "filter_even", "map_to_dict", "transpose", "moving_average"},
            "実務データ処理": {"total_revenue", "average_satisfaction", "overdue_tasks", "department_totals", "best_employee", "normalize_scores", "monthly_summary", "detect_low_stock", "create_invoice_lines", "calc_kpi"},
            "アルゴリズム": {"binary_search", "is_palindrome", "is_valid_parentheses", "longest_word", "compress_chars", "expand_chars", "rotate_list", "chunk_list", "merge_sorted", "two_sum"},
            "ミニアプリ実装": {"add_task", "complete_task", "delete_task", "filter_tasks", "sort_tasks_by_due", "calc_progress", "dashboard_metrics", "overdue_rate", "priority_summary", "recommend_next_action"},
        }
        for label, names in groups.items():
            if fn in names:
                return f"このレッスンでは、{label}の考え方を学んでほしいです。入力を受け取り、条件分岐や反復処理で整理して、期待される形で返す流れが重要です。"
        return "このレッスンでは、関数として処理を切り出し、再利用しやすい形で実装することを学んでほしいです。"
    return ""


def format_example_value(v: Any) -> str:
    return repr(v)


def build_detailed_instruction(ms: dict[str, Any]) -> str:
    # 元の短い問題文だけでは不足しやすいため、判定条件が読み取れる補足説明を作る。
    if ms["type"] == "value":
        return (
            "やること:\n"
            f"- `{ms['var']}` という名前の変数を作ります。\n"
            f"- その変数に `{format_example_value(ms['exp'])}` を入れてください。\n"
            "- 変数名を変えずに、そのまま使ってください。"
        )

    if ms["type"] == "fn":
        lines = [
            "やること:",
            f"- `{ms['fn']}` という関数を作ります。",
            "- 関数名は変えないでください。",
            "- 次の入出力例を満たすように実装してください。",
        ]
        for t in ms["tests"]:
            args = t["args"] if isinstance(t["args"], tuple) else tuple(t["args"])
            lines.append(f"- `{ms['fn']}{args}` の結果が `{format_example_value(t['out'])}` になること")
        return "\n".join(lines)

    if ms["type"] == "st":
        required = ", ".join(f"`st.{name}`" for name in ms["calls"])
        return (
            "やること:\n"
            "- Streamlit の部品を使ってコードを書きます。\n"
            f"- この問題では {required} をすべて1回以上使ってください。\n"
            "- 画面の見た目は自由ですが、指定された部品が含まれている必要があります。"
        )

    return ""


def inject_styles() -> None:
    # CSS を直接埋め込み、アプリ全体の見た目を調整する。
    st.markdown("""
        <style>
            :root {--bg:#f2f6fb;--muted:#58677a;--ok-bg:#e8f7ec;--ok-border:#169b4d;--brand:#0b6bcb;--brand-hover:#0957a6;}
            .stApp{background:radial-gradient(circle at 8% 0%,#eef6ff 0%,var(--bg) 52%);}
            .hero{background:linear-gradient(115deg,#00395f 0%,#0068a9 80%);border-radius:16px;color:#fff;padding:20px 24px;margin-bottom:14px;box-shadow:0 10px 24px rgba(0,45,79,.22);}
            .hero h1{margin:0;font-size:28px;letter-spacing:.3px;}
            .hero p{margin:6px 0 0;font-size:15px;color:#d7e9ff;}
            .small-note{color:var(--muted);font-size:13px;}
            .reward{background:var(--ok-bg);border-left:5px solid var(--ok-border);border-radius:8px;padding:10px 12px;margin-top:10px;color:#0e6b35;font-weight:600;}
            .stButton button[kind="primary"]{background:var(--brand);border-color:var(--brand);color:#fff;}
            .stButton button[kind="primary"]:hover{background:var(--brand-hover);border-color:var(--brand-hover);color:#fff;}
        </style>
    """, unsafe_allow_html=True)


def render_sidebar() -> None:
    # 左側のサイドバーに進捗と現在周辺のミッション一覧を表示する。
    st.sidebar.title("学習ロードマップ")
    total = len(MISSIONS)
    page = st.session_state.current // 10
    s = page * 10
    e = min(s + 10, total)
    st.sidebar.caption(f"表示中: {s + 1} - {e} / {total}")
    for i in range(s, e):
        icon = "[CLEAR]" if is_cleared(i) else "[TODO]"
        st.sidebar.write(f"{icon} {MISSIONS[i]['title']}")
    st.sidebar.markdown("---")
    st.sidebar.metric("進捗", f"{int(mission_progress() * 100)}%")
    st.sidebar.progress(mission_progress())
    if st.sidebar.button("最初からやり直す"):
        st.session_state.current = 0
        st.session_state.cleared = set()
        st.rerun()


def render_mission(i: int) -> None:
    # 現在のミッション本文、入力欄、ヒント、模範解答を表示する。
    ms = MISSIONS[i]
    st.subheader(ms["title"])
    st.write(ms["description"])
    st.info(ms["instruction"])
    st.markdown(build_detailed_instruction(ms))
    code = st.text_area("あなたの回答コード", height=200, key=f"code_{ms['id']}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("次のミッション", key=f"next_top_{ms['id']}", use_container_width=True):
            st.session_state.current = min(len(MISSIONS) - 1, st.session_state.current + 1)
            st.session_state.feedback = None
            st.rerun()
    with c2:
        if st.button("ヒントを見る", key=f"hint_{ms['id']}", use_container_width=True):
            st.warning(ms["hint"])
    with st.expander("想定解を見る"):
        st.code(build_sample_solution(ms), language="python")
        st.markdown("**このレッスンで学んでほしいこと**")
        st.write(build_lesson_explanation(ms))


def render_navigation() -> None:
    # 画面下部の主要操作。右下に判定ボタンを置いている。
    p, n = st.columns(2)
    current_mission = MISSIONS[st.session_state.current]
    with p:
        if st.button("前のミッション", use_container_width=True):
            st.session_state.current = max(0, st.session_state.current - 1)
            st.session_state.feedback = None
            st.rerun()
    with n:
        if st.button("判定する", key=f"judge_{current_mission['id']}", use_container_width=True, type="primary"):
            # text_area に入力された内容は、session_state から取り出せる。
            code = st.session_state.get(f"code_{current_mission['id']}", "")
            ok, msg = evaluate_mission(st.session_state.current, code)
            if ok:
                # set は重複しないので、同じミッションを何度追加しても1件のまま。
                st.session_state.cleared.add(current_mission["id"])
                st.session_state.feedback = {
                    "kind": "success",
                    "message": f"ミッションクリア: {msg}",
                    "reward": current_mission["reward"],
                }
                st.balloons()
            else:
                st.session_state.feedback = {
                    "kind": "error",
                    "message": f"未クリア: {msg}",
                    "reward": None,
                }
            st.rerun()


def render_finish_message() -> None:
    # 全ミッションクリア時だけ、完了メッセージを出す。
    if len(st.session_state.cleared) == len(MISSIONS):
        st.markdown("---")
        st.success("全100ミッションクリアです。Pythonアプリ開発の基礎を完了しました。")
        st.snow()


def render_feedback() -> None:
    # 判定結果は画面下部にまとめて表示する。
    feedback = st.session_state.feedback
    if not feedback:
        return
    st.markdown("---")
    if feedback["kind"] == "success":
        st.success(feedback["message"])
        if feedback["reward"]:
            st.markdown(f"<div class='reward'>報酬: {feedback['reward']}</div>", unsafe_allow_html=True)
    else:
        st.error(feedback["message"])


def main() -> None:
    # Streamlit アプリの表示順をまとめた入口。
    init_state()
    inject_styles()
    st.markdown("""
        <div class="hero">
            <h1>Python Mission Quest</h1>
            <p>一般的な会社員向け: 1画面1ミッションで進める、業務に活かすPython入門</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<p class='small-note'>現在のミッション: {st.session_state.current + 1} / {len(MISSIONS)}</p>", unsafe_allow_html=True)
    render_sidebar()
    render_mission(st.session_state.current)
    render_navigation()
    render_finish_message()
    render_feedback()


if __name__ == "__main__":
    main()
