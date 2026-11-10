from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]

def test_core_config_files_exist():
    for name in ("finance", "risk_limits", "risk_weights", "kri_catalogue", "sources"):
        assert (ROOT / "config" / f"{name}.yaml").is_file()

def test_technology_sector_is_configured():
    with (ROOT / "config" / "sources.yaml").open(encoding="utf-8") as f:
        assert yaml.safe_load(f)["sector"] == "technology"

def test_single_name_limits_are_ordered():
    with (ROOT / "config" / "risk_limits.yaml").open(encoding="utf-8") as f:
        limits = yaml.safe_load(f)["single_name"]
    assert 0 < limits["soft_limit_fraction"] < limits["hard_limit_fraction"] < 1

def test_synthetic_disclosure_in_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "entirely synthetic" in readme
    assert "not regulatory-compliant" in readme
