"""
RetailPulse ETL — Data Validator
Validates rows from CSV before inserting into PostgreSQL.
"""

from dataclasses import dataclass, field
from datetime import date
from loguru import logger


@dataclass
class ValidationResult:
    valid_rows: list = field(default_factory=list)
    invalid_rows: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.valid_rows) + len(self.invalid_rows)

    @property
    def pass_rate(self) -> float:
        return len(self.valid_rows) / self.total * 100 if self.total > 0 else 0


REQUIRED_COLUMNS = [
    "order_id", "order_date", "region", "category",
    "product_name", "quantity", "unit_price", "discount", "revenue", "profit",
]

VALID_REGIONS = {"East", "West", "Central", "South"}
VALID_CATEGORIES = {"Technology", "Furniture", "Office Supplies"}
VALID_SEGMENTS = {"Consumer", "Corporate", "Home Office", None, ""}


def validate_row(row: dict, row_num: int) -> tuple[bool, str]:
    """Validate a single sales row. Returns (is_valid, error_message)."""

    # Check required columns
    for col in REQUIRED_COLUMNS:
        if col not in row or row[col] is None or str(row[col]).strip() == "":
            return False, f"Row {row_num}: missing required field '{col}'"

    # Validate order_date
    try:
        if isinstance(row["order_date"], str):
            date.fromisoformat(row["order_date"])
    except ValueError:
        return False, f"Row {row_num}: invalid order_date '{row['order_date']}'"

    # Validate region
    if row["region"] not in VALID_REGIONS:
        return False, f"Row {row_num}: unknown region '{row['region']}'"

    # Validate category
    if row["category"] not in VALID_CATEGORIES:
        return False, f"Row {row_num}: unknown category '{row['category']}'"

    # Validate numeric fields
    try:
        quantity = int(row["quantity"])
        if quantity <= 0:
            return False, f"Row {row_num}: quantity must be > 0, got {quantity}"
    except (ValueError, TypeError):
        return False, f"Row {row_num}: invalid quantity '{row['quantity']}'"

    try:
        unit_price = float(row["unit_price"])
        if unit_price < 0:
            return False, f"Row {row_num}: unit_price must be >= 0"
    except (ValueError, TypeError):
        return False, f"Row {row_num}: invalid unit_price '{row['unit_price']}'"

    try:
        discount = float(row["discount"])
        if not (0 <= discount <= 1):
            return False, f"Row {row_num}: discount must be between 0 and 1, got {discount}"
    except (ValueError, TypeError):
        return False, f"Row {row_num}: invalid discount '{row['discount']}'"

    # Validate segment (optional)
    if row.get("segment") not in VALID_SEGMENTS:
        return False, f"Row {row_num}: unknown segment '{row.get('segment')}'"

    return True, ""


def validate_dataframe(df) -> ValidationResult:
    """Validate all rows in a pandas DataFrame."""
    result = ValidationResult()

    for i, row in df.iterrows():
        is_valid, error = validate_row(row.to_dict(), i + 2)  # +2 for 1-index + header
        if is_valid:
            result.valid_rows.append(row.to_dict())
        else:
            result.invalid_rows.append(row.to_dict())
            result.errors.append(error)
            logger.warning(error)

    logger.info(
        f"Validation complete: {len(result.valid_rows)} valid, "
        f"{len(result.invalid_rows)} invalid ({result.pass_rate:.1f}% pass rate)"
    )
    return result
