"""
Data Validation Module
Provides validation functions for football statistics data
"""

import re
from typing import Any, Optional, List, Dict
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class DataValidator:
    """
    Validates data before database insertion
    """

    # Valid league names
    VALID_LEAGUES = {
        'ENG-Premier League',
        'ESP-La Liga',
        'GER-Bundesliga',
        'ITA-Serie A',
        'FRA-Ligue 1',
    }

    # Season format: YYYY or YYZZ (e.g., '2021' or '2122')
    SEASON_PATTERN = re.compile(r'^\d{2}(\d{2})?$')

    # Valid data sources
    VALID_SOURCES = {
        'fbref',
        'fotmob',
        'understat',
        'whoscored',
        'sofascore',
        'espn',
        'clubelo',
        'matchhistory',
        'sofifa',
    }

    @staticmethod
    def validate_league(league: str, allow_none: bool = False) -> bool:
        """
        Validate league name

        Args:
            league: League name to validate
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if league is None and allow_none:
            return True

        if not isinstance(league, str):
            raise ValidationError(f"League must be string, got {type(league)}")

        if league not in DataValidator.VALID_LEAGUES:
            raise ValidationError(
                f"Invalid league '{league}'. Must be one of: {DataValidator.VALID_LEAGUES}"
            )

        return True

    @staticmethod
    def validate_season(season: str, allow_none: bool = False) -> bool:
        """
        Validate season format

        Args:
            season: Season to validate (e.g., '2021', '2122')
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if season is None and allow_none:
            return True

        if not isinstance(season, str):
            raise ValidationError(f"Season must be string, got {type(season)}")

        if not DataValidator.SEASON_PATTERN.match(season):
            raise ValidationError(
                f"Invalid season format '{season}'. Must be YYYY or YYZZ (e.g., '2021' or '2122')"
            )

        return True

    @staticmethod
    def validate_data_source(source: str, allow_none: bool = False) -> bool:
        """
        Validate data source name

        Args:
            source: Data source to validate
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if source is None and allow_none:
            return True

        if not isinstance(source, str):
            raise ValidationError(f"Data source must be string, got {type(source)}")

        if source not in DataValidator.VALID_SOURCES:
            raise ValidationError(
                f"Invalid data source '{source}'. Must be one of: {DataValidator.VALID_SOURCES}"
            )

        return True

    @staticmethod
    def validate_numeric(
        value: Any,
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_none: bool = True,
    ) -> bool:
        """
        Validate numeric value

        Args:
            value: Value to validate
            field_name: Name of the field (for error messages)
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if value is None and allow_none:
            return True

        if value is None and not allow_none:
            raise ValidationError(f"{field_name} cannot be None")

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name} must be numeric, got {type(value)}")

        if min_value is not None and numeric_value < min_value:
            raise ValidationError(
                f"{field_name} must be >= {min_value}, got {numeric_value}"
            )

        if max_value is not None and numeric_value > max_value:
            raise ValidationError(
                f"{field_name} must be <= {max_value}, got {numeric_value}"
            )

        return True

    @staticmethod
    def validate_percentage(
        value: Any,
        field_name: str,
        allow_none: bool = True,
    ) -> bool:
        """
        Validate percentage value (0-100)

        Args:
            value: Value to validate
            field_name: Name of the field
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        return DataValidator.validate_numeric(
            value, field_name, min_value=0, max_value=100, allow_none=allow_none
        )

    @staticmethod
    def validate_xg(
        value: Any,
        field_name: str,
        allow_none: bool = True,
    ) -> bool:
        """
        Validate xG (expected goals) value

        Args:
            value: Value to validate
            field_name: Name of the field
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        return DataValidator.validate_numeric(
            value, field_name, min_value=0, allow_none=allow_none
        )

    @staticmethod
    def validate_date(
        value: Any,
        field_name: str,
        allow_none: bool = True,
    ) -> bool:
        """
        Validate date value

        Args:
            value: Value to validate (datetime, date, or string)
            field_name: Name of the field
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if value is None and allow_none:
            return True

        if value is None and not allow_none:
            raise ValidationError(f"{field_name} cannot be None")

        if isinstance(value, (datetime, date)):
            return True

        if isinstance(value, str):
            # Try to parse as ISO format
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True
            except ValueError:
                raise ValidationError(f"{field_name} has invalid date format: {value}")

        raise ValidationError(f"{field_name} must be datetime, date, or ISO string")

    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        allow_none: bool = True,
        allow_empty: bool = True,
    ) -> bool:
        """
        Validate string value

        Args:
            value: Value to validate
            field_name: Name of the field
            min_length: Minimum string length
            max_length: Maximum string length
            allow_none: Whether to allow None values
            allow_empty: Whether to allow empty strings

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        if value is None and allow_none:
            return True

        if value is None and not allow_none:
            raise ValidationError(f"{field_name} cannot be None")

        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be string, got {type(value)}")

        if not allow_empty and len(value) == 0:
            raise ValidationError(f"{field_name} cannot be empty")

        if min_length is not None and len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters"
            )

        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters"
            )

        return True

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required_fields: List[str],
    ) -> bool:
        """
        Validate that all required fields are present

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Returns:
            True if all required fields present

        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        return True

    @staticmethod
    def validate_coordinates(
        x: Any,
        y: Any,
        field_name: str = "coordinate",
        min_value: float = 0,
        max_value: float = 100,
        allow_none: bool = True,
    ) -> bool:
        """
        Validate coordinate values (e.g., shot location)

        Args:
            x: X coordinate
            y: Y coordinate
            field_name: Base field name for error messages
            min_value: Minimum coordinate value
            max_value: Maximum coordinate value
            allow_none: Whether to allow None values

        Returns:
            True if valid

        Raises:
            ValidationError: If invalid
        """
        DataValidator.validate_numeric(
            x, f"{field_name}_x", min_value=min_value, max_value=max_value, allow_none=allow_none
        )
        DataValidator.validate_numeric(
            y, f"{field_name}_y", min_value=min_value, max_value=max_value, allow_none=allow_none
        )
        return True

    @staticmethod
    def clean_numeric(value: Any) -> Optional[float]:
        """
        Clean and convert value to numeric, handling common issues

        Args:
            value: Value to clean

        Returns:
            Numeric value or None
        """
        if value is None or value == '':
            return None

        # Handle pandas NA
        try:
            import pandas as pd
            if pd.isna(value):
                return None
        except ImportError:
            pass

        # Handle string values
        if isinstance(value, str):
            # Remove common formatting
            value = value.strip().replace(',', '').replace('%', '')

            # Handle empty after cleaning
            if value == '' or value == '-':
                return None

        # Convert to float
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.warning(f"Could not convert value to numeric: {value}")
            return None

    @staticmethod
    def clean_string(value: Any) -> Optional[str]:
        """
        Clean string value

        Args:
            value: Value to clean

        Returns:
            Cleaned string or None
        """
        if value is None or value == '':
            return None

        # Handle pandas NA
        try:
            import pandas as pd
            if pd.isna(value):
                return None
        except ImportError:
            pass

        # Convert to string and strip
        str_value = str(value).strip()

        # Return None for empty strings after stripping
        if str_value == '' or str_value == '-':
            return None

        return str_value

    @staticmethod
    def validate_batch(
        data: List[Dict[str, Any]],
        required_fields: List[str],
        validators: Optional[Dict[str, callable]] = None,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate a batch of records

        Args:
            data: List of data dictionaries
            required_fields: List of required field names
            validators: Dictionary mapping field names to validator functions

        Returns:
            Tuple of (valid_records, invalid_records)
        """
        valid_records = []
        invalid_records = []

        for idx, record in enumerate(data):
            try:
                # Check required fields
                DataValidator.validate_required_fields(record, required_fields)

                # Run custom validators if provided
                if validators:
                    for field_name, validator_func in validators.items():
                        if field_name in record:
                            validator_func(record[field_name], field_name)

                valid_records.append(record)

            except ValidationError as e:
                logger.warning(f"Validation failed for record {idx}: {e}")
                invalid_records.append({
                    'record': record,
                    'error': str(e),
                    'index': idx,
                })

        logger.info(
            f"Validated {len(data)} records: {len(valid_records)} valid, "
            f"{len(invalid_records)} invalid"
        )

        return valid_records, invalid_records
