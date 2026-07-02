import pandas as pd

from research_metadata_toolkit.toolkit.encoding import fix_encoding


def test_fix_encoding_preserves_columns_and_writes_output(tmp_path) -> None:
    input_file = tmp_path / "input.xlsx"
    output_file = tmp_path / "output.xlsx"
    pd.DataFrame({"Title": ["FranÃ§ais"], "Authors": ["AnaÃ¯s"], "Other": ["x"]}).to_excel(input_file, index=False)

    result = fix_encoding(input_file, output_file)
    output = pd.read_excel(result)

    assert output.loc[0, "Title"] == "Français"
    assert output.loc[0, "Authors"] == "Anaïs"
    assert output.loc[0, "Other"] == "x"
