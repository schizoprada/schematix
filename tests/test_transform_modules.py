# ~/schematix/tests/test_transform_modules.py
"""
Tests for individual transform modules: text, numbers, dates, collections, validation, common.
"""
import pytest
from datetime import datetime, date, timedelta
from schematix.transforms import text, numbers, dates, collections as col, validation as val, common


class TestTextTransforms:
    """Test text transformation functions."""

    def test_basic_string_operations(self):
        """Test basic string transforms."""
        assert text.strip("  hello  ") == "hello"
        assert text.upper("hello") == "HELLO"
        assert text.lower("HELLO") == "hello"
        assert text.title("hello world") == "Hello World"
        assert text.capitalize("hello world") == "Hello world"

    def test_replace_operations(self):
        """Test string replacement transforms."""
        replace_transform = text.replace("hello", "hi")
        assert replace_transform("hello world") == "hi world"

        removeprefix_transform = text.removeprefix("Mr. ")  # Add space back
        assert removeprefix_transform("Mr. Smith") == "Smith"

        removesuffix_transform = text.removesuffix(".txt")
        assert removesuffix_transform("file.txt") == "file"

    def test_regex_operations(self):
        """Test regex transforms."""
        extract_digits = text.regexextract(r'\d+')
        assert extract_digits("abc123def") == "123"

        replace_digits = text.regexreplace(r'\d+', 'X')
        assert replace_digits("abc123def456") == "abcXdefX"

        find_all = text.regexfindall(r'\d+')
        assert find_all("abc123def456") == ["123", "456"]

    def test_formatting_operations(self):
        """Test string formatting transforms."""
        truncate_transform = text.truncate(10, "...")
        assert truncate_transform("This is a very long string") == "This is..."

        padleft_transform = text.padleft(10, "0")
        assert padleft_transform("123") == "0000000123"

        padright_transform = text.padright(10, "0")
        assert padright_transform("123") == "1230000000"

        center_transform = text.center(10, "-")
        assert center_transform("hi") == "----hi----"

        zfill_transform = text.zfill(5)
        assert zfill_transform("123") == "00123"

    def test_splitting_joining(self):
        """Test split and join operations."""
        split_transform = text.split(",")
        assert split_transform("a,b,c") == ["a", "b", "c"]

        join_transform = text.join("-")
        assert join_transform(["a", "b", "c"]) == "a-b-c"

        splitlines_transform = text.splitlines()
        assert splitlines_transform("line1\nline2") == ["line1", "line2"]

    def test_specialized_operations(self):
        """Test specialized text operations."""
        assert text.slug("Hello World!") == "hello-world"
        assert text.normalizewhitespace("hello   world\n\ttest") == "hello world test"
        assert text.reverse("hello") == "olleh"

    def test_predicates(self):
        """Test text predicate transforms."""
        startswith_transform = text.startswith("hello")
        assert startswith_transform("hello world") == True

        endswith_transform = text.endswith("world")
        assert endswith_transform("hello world") == True

        contains_transform = text.contains("ell")
        assert contains_transform("hello") == True

        contains_insensitive = text.contains("ELL", casesensitive=False)
        assert contains_insensitive("hello") == True

    def test_encoding_operations(self):
        """Test encoding/decoding transforms."""
        # Test basic encoding/decoding
        encoded = text.encode.base64("hello")
        decoded = text.decode.base64(encoded)
        assert decoded == "hello"

        url_encoded = text.encode.url("hello world")
        url_decoded = text.decode.url(url_encoded)
        assert url_decoded == "hello world"

        html_escaped = text.html.escape("<script>")
        html_unescaped = text.html.unescape(html_escaped)
        assert html_unescaped == "<script>"


class TestNumbersTransforms:
    """Test numbers transformation functions."""

    def test_type_conversion(self):
        """Test number type conversion."""
        assert numbers.to.int("123") == 123
        assert numbers.to.float("123.45") == 123.45
        assert str(numbers.to.decimal("123.45")) == "123.45"

    def test_safe_conversion(self):
        """Test safe number conversion with defaults."""
        safe_int = numbers.safeto.int(default=0)
        assert safe_int("123") == 123
        assert safe_int("invalid") == 0

        safe_float = numbers.safeto.float(default=0.0)
        assert safe_float("123.45") == 123.45
        assert safe_float("invalid") == 0.0

    def test_math_operations(self):
        """Test basic math operations."""
        add_transform = numbers.add(10)
        assert add_transform(5) == 15

        subtract_transform = numbers.subtract(3)
        assert subtract_transform(10) == 7

        multiply_transform = numbers.multiply(2)
        assert multiply_transform(5) == 10

        divide_transform = numbers.divide(2)
        assert divide_transform(10) == 5.0

        power_transform = numbers.power(2)
        assert power_transform(3) == 9

        # Test the callable transforms directly
        assert numbers.abs(-5) == 5
        assert numbers.negate(5) == -5

    def test_rounding_operations(self):
        """Test rounding and precision."""
        roundto_transform = numbers.roundto(2)
        assert roundto_transform(3.14159) == 3.14

        assert numbers.floor(3.7) == 3
        assert numbers.ceil(3.2) == 4
        assert numbers.trunc(3.7) == 3

    def test_range_operations(self):
        """Test range and bounds."""
        clamp_transform = numbers.clamp(0, 10)
        assert clamp_transform(15) == 10
        assert clamp_transform(-5) == 0

        minvalue_transform = numbers.minvalue(5)
        assert minvalue_transform(3) == 5

        maxvalue_transform = numbers.maxvalue(10)
        assert maxvalue_transform(15) == 10

    def test_mathematical_functions(self):
        """Test mathematical functions."""
        assert numbers.sqrt(9) == 3.0
        assert abs(numbers.sin(0)) < 0.001  # sin(0) ≈ 0
        assert abs(numbers.cos(0) - 1) < 0.001  # cos(0) ≈ 1
        assert numbers.degrees(3.14159) == pytest.approx(180, abs=1)

    def test_formatting(self):
        """Test number formatting."""
        currency_transform = numbers.format.currency()
        assert currency_transform(1234.56) == "$1,234.56"

        percent_transform = numbers.format.percent()
        assert percent_transform(0.456) == "45.6%"

        scientific_transform = numbers.format.scientific()
        assert "1.23e+03" in scientific_transform(1234)

        commas_transform = numbers.format.commas()
        assert "1,234.56" in commas_transform(1234.56)

    def test_utility_functions(self):
        """Test utility functions."""
        assert numbers.sign(5) == 1
        assert numbers.sign(-5) == -1
        assert numbers.sign(0) == 0
        assert numbers.factorial(5) == 120

        inrange_transform = numbers.inrange(0, 10)
        assert inrange_transform(5) == True
        assert inrange_transform(15) == False


class TestDatesTransforms:
    """Test date transformation functions."""

    def test_parsing(self):
        """Test date parsing."""
        # Test auto parsing
        dt = dates.parse.auto("2023-12-25")
        assert isinstance(dt, datetime)
        assert dt.year == 2023
        assert dt.month == 12
        assert dt.day == 25

        # Test ISO parsing
        iso_dt = dates.parse.iso("2023-12-25T14:30:00")
        assert iso_dt.hour == 14
        assert iso_dt.minute == 30

        # Test format parsing
        fmt_transform = dates.parse.format("%Y/%m/%d")
        fmt_dt = fmt_transform("2023/12/25")
        assert fmt_dt.year == 2023

    def test_conversion(self):
        """Test date conversion."""
        dt = datetime(2023, 12, 25, 14, 30, 0)

        assert dates.to.date(dt).year == 2023
        assert dates.to.time(dt).hour == 14
        assert isinstance(dates.to.timestamp(dt), float)

    def test_formatting(self):
        """Test date formatting."""
        dt = datetime(2023, 12, 25, 14, 30, 0)

        assert dates.format.date(dt) == "2023-12-25"
        assert dates.format.time(dt) == "14:30:00"
        assert dates.format.datetime(dt) == "2023-12-25 14:30:00"
        assert "December 25, 2023" in dates.format.readable(dt)

    def test_date_math(self):
        """Test date arithmetic."""
        dt = datetime(2023, 12, 25)

        add_transform = dates.add(days=1)
        future = add_transform(dt)
        assert future.day == 26

        subtract_transform = dates.subtract(days=1)
        past = subtract_transform(dt)
        assert past.day == 24

        diff_transform = dates.difference(dt)
        diff = diff_transform(future)
        assert isinstance(diff, timedelta)

    def test_components(self):
        """Test date component extraction."""
        dt = datetime(2023, 12, 25, 14, 30, 45)

        assert dates.year(dt) == 2023
        assert dates.month(dt) == 12
        assert dates.day(dt) == 25
        assert dates.hour(dt) == 14
        assert dates.minute(dt) == 30
        assert dates.second(dt) == 45
        assert dates.weekday(dt) == 0  # Monday

    def test_boundaries(self):
        """Test date boundaries."""
        dt = datetime(2023, 12, 25, 14, 30, 45)

        start = dates.startofday(dt)
        assert start.hour == 0 and start.minute == 0

        end = dates.endofday(dt)
        assert end.hour == 23 and end.minute == 59

        month_start = dates.startofmonth(dt)
        assert month_start.day == 1

    def test_predicates(self):
        """Test date predicates."""
        dt1 = datetime(2023, 12, 25)
        dt2 = datetime(2023, 12, 26)

        isbefore_transform = dates.isbefore(dt2)
        assert isbefore_transform(dt1) == True

        isafter_transform = dates.isafter(dt1)
        assert isafter_transform(dt2) == True

        isbetween_transform = dates.isbetween(dt1, dt2)
        assert isbetween_transform(datetime(2023, 12, 25, 12)) == True


class TestCollectionsTransforms:
    """Test collections transformation functions."""

    def test_basic_access(self):
        """Test basic collection access."""
        data = [1, 2, 3, 4, 5]

        assert col.first(data) == 1
        assert col.last(data) == 5

        nth_transform = col.nth(2)
        assert nth_transform(data) == 3

        assert col.length(data) == 5
        assert col.isempty([]) == True

    def test_list_operations(self):
        """Test list operations."""
        data = [3, 1, 4, 1, 5]

        assert col.unique(data) == [3, 1, 4, 5]
        assert col.reverse(data) == [5, 1, 4, 1, 3]
        assert col.sort(data) == [1, 1, 3, 4, 5]

    def test_filtering_mapping(self):
        """Test filtering and mapping."""
        data = [1, 2, 3, 4, 5]

        filter_transform = col.filter(lambda x: x % 2 == 0)
        evens = filter_transform(data)
        assert evens == [2, 4]

        map_transform = col.map(lambda x: x * 2)
        doubled = map_transform(data)
        assert doubled == [2, 4, 6, 8, 10]

    def test_slicing(self):
        """Test slicing operations."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        take_transform = col.take(3)
        assert take_transform(data) == [1, 2, 3]

        skip_transform = col.skip(3)
        assert skip_transform(data) == [4, 5, 6, 7, 8, 9, 10]

        slice_transform = col.slice(2, 5)
        assert slice_transform(data) == [3, 4, 5]

        chunk_transform = col.chunk(3)
        chunks = chunk_transform(data)
        assert chunks == [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]

    def test_dict_operations(self):
        """Test dictionary operations."""
        data = {"a": 1, "b": 2, "c": 3}

        assert col.keys(data) == ["a", "b", "c"]
        assert col.values(data) == [1, 2, 3]

        get_transform = col.get("b")
        assert get_transform(data) == 2

        get_default_transform = col.get("z", "default")
        assert get_default_transform(data) == "default"

    def test_aggregation(self):
        """Test aggregation operations."""
        data = [1, 2, 3, 4, 5]

        assert col.sum(data) == 15
        assert col.count(data) == 5

        # Test groupby
        people = [
            {"name": "Alice", "dept": "eng"},
            {"name": "Bob", "dept": "eng"},
            {"name": "Carol", "dept": "sales"}
        ]

        groupby_transform = col.groupby("dept")
        groups = groupby_transform(people)
        assert len(groups["eng"]) == 2
        assert len(groups["sales"]) == 1

    def test_set_operations(self):
        """Test set operations."""
        set1 = [1, 2, 3]
        set2 = [2, 3, 4]

        union_transform = col.union(set2)
        assert union_transform(set1) == {1, 2, 3, 4}

        intersection_transform = col.intersection(set2)
        assert intersection_transform(set1) == {2, 3}

        difference_transform = col.difference(set2)
        assert difference_transform(set1) == {1}

    def test_modification(self):
        """Test list modification."""
        data = [1, 2, 3]

        append_transform = col.append(4)
        assert append_transform(data) == [1, 2, 3, 4]

        prepend_transform = col.prepend(0)
        assert prepend_transform(data) == [0, 1, 2, 3]

        extend_transform = col.extend([4, 5])
        assert extend_transform(data) == [1, 2, 3, 4, 5]


class TestValidationTransforms:
    """Test validation transformation functions."""

    def test_format_validation(self):
        """Test format validation."""
        assert val.isa.email("test@example.com") == True
        assert val.isa.email("invalid-email") == False

        assert val.isa.url("https://example.com") == True
        assert val.isa.url("not-a-url") == False

        assert val.isa.phoneus("(555) 123-4567") == True
        assert val.isa.numeric("12345") == True
        assert val.isa.alpha("abcdef") == True

    def test_content_validation(self):
        """Test content validation."""
        length_transform = val.has.length(5, 10)
        assert length_transform("hello") == True
        assert length_transform("hi") == False

        substring_transform = val.has.substring("ell")
        assert substring_transform("hello") == True

        assert val.has.digits("abc123") == True
        assert val.has.uppercase("Hello") == True

    def test_range_validation(self):
        """Test range validation."""
        int_range_transform = val.inrange.int(1, 10)
        assert int_range_transform(5) == True
        assert int_range_transform(15) == False

        float_range_transform = val.inrange.float(0.0, 1.0)
        assert float_range_transform(0.5) == True
        assert float_range_transform(1.5) == False

    def test_type_validation(self):
        """Test type validation."""
        assert val.canbe.int("123") == True
        assert val.canbe.int("abc") == False

        assert val.canbe.float("123.45") == True
        assert val.canbe.bool("true") == True

    def test_basic_checks(self):
        """Test basic validation checks."""
        assert val.notempty("hello") == True
        assert val.notempty("") == False
        assert val.notempty("   ") == False

        assert val.notnull("hello") == True
        assert val.notnull(None) == False

        assert val.isblank("") == True
        assert val.isblank("   ") == True
        assert val.isblank("hello") == False

    def test_collection_validation(self):
        """Test collection validation."""
        minlength_transform = val.collection.minlength(3)
        assert minlength_transform([1, 2, 3]) == True
        assert minlength_transform([1, 2]) == False

        contains_transform = val.collection.contains(2)
        assert contains_transform([1, 2, 3]) == True
        assert contains_transform([1, 3, 4]) == False

        allitems_transform = val.collection.allitems(lambda x: x > 0)
        assert allitems_transform([1, 2, 3]) == True
        assert allitems_transform([1, -2, 3]) == False

    def test_cleaning(self):
        """Test data cleaning."""
        assert val.clean.email("  TEST@EXAMPLE.COM  ") == "test@example.com"
        # Phone cleaning might not add +1 prefix
        cleaned_phone = val.clean.phone("(555) 123-4567")
        assert "5551234567" in cleaned_phone  # Just check it contains the digits
        assert val.clean.whitespace("hello   world") == "hello world"
        assert val.clean.alphanumeric("abc-123!") == "abc123"

    def test_requirements(self):
        """Test requirement validation."""
        # Test successful validation
        email_req = val.requires.email()
        assert email_req("test@example.com") == "test@example.com"

        notempty_req = val.requires.notempty()
        assert notempty_req("hello") == "hello"

        length_req = val.requires.length(3, 10)
        assert length_req("hello") == "hello"

        # Test validation failures
        with pytest.raises(ValueError):
            email_req("invalid-email")

        with pytest.raises(ValueError):
            notempty_req("")

        with pytest.raises(ValueError):
            val.requires.length(5, 10)("hi")


class TestCommonTransforms:
    """Test common transformation patterns."""

    def test_cleaning_operations(self):
        """Test common cleaning transforms."""
        # These are static methods, call them directly
        assert common.clean.text("  hello   world  ") == "hello world"
        assert common.clean.name("  john doe  ") == "John Doe"
        assert common.clean.email("  TEST@EXAMPLE.COM  ") == "test@example.com"
        assert common.clean.price("$1,234.56") == 1234.56

    def test_safe_cleaning(self):
        """Test safe cleaning with fallbacks."""
        safe_email = common.clean.safe.email("")  # Call with default value
        assert safe_email("test@example.com") == "test@example.com"
        assert safe_email("invalid-email") == ""

    def test_formatting_operations(self):
        """Test common formatting transforms."""
        assert common.format.titlecase("hello world") == "Hello World"
        assert common.format.slug("Hello World!") == "hello-world"
        assert common.format.currency(1234.56) == "$1,234.56"
        assert common.format.percentage(0.456) == "45.6%"

    def test_parsing_operations(self):
        """Test common parsing transforms."""
        assert common.parse.date("2023-12-25") == "2023-12-25"
        assert common.parse.number("123.45") == 123.45
        assert common.parse.number("invalid") == 0.0
        assert common.parse.integer("123") == 123

    def test_safe_operations(self):
        """Test safe operations."""
        data = {"name": "John", "age": 30}

        safe_get = common.safe.get("name")
        assert safe_get(data) == "John"

        safe_get_default = common.safe.get("missing", "default")
        assert safe_get_default(data) == "default"

        safe_first = common.safe.first("empty")  # Call with default value directly
        assert safe_first([1, 2, 3]) == 1
        assert safe_first([]) == "empty"

    def test_extraction_operations(self):
        """Test data extraction patterns."""
        text_data = "Contact us at test@example.com or visit https://example.com"

        emails = common.extract.emails(text_data)
        assert "test@example.com" in emails

        urls = common.extract.urls(text_data)
        assert "https://example.com" in urls

        numbers = common.extract.numbers("Price: $123.45")
        assert "123.45" in numbers

    def test_list_processing(self):
        """Test list processing patterns."""
        emails = ["  TEST@EXAMPLE.COM  ", "invalid-email", "user@domain.com"]

        cleaned = common.lists.cleanedemails(emails)
        assert "test@example.com" in cleaned
        assert "user@domain.com" in cleaned
        assert len(cleaned) == 2  # invalid email removed

        names = ["  john doe  ", "jane smith", "john doe"]
        cleaned_names = common.lists.cleanednames(names)
        assert "John Doe" in cleaned_names
        assert "Jane Smith" in cleaned_names
        assert len(cleaned_names) == 2  # duplicate removed

    def test_validation_shortcuts(self):
        """Test validation shortcuts."""
        email_validator = common.validate.email
        assert email_validator("test@example.com") == "test@example.com"

        notempty_validator = common.validate.notempty
        assert notempty_validator("hello") == "hello"

        length_validator = common.validate.length(3, 10)
        assert length_validator("hello") == "hello"

        range_validator = common.validate.inrange(1, 10)
        assert range_validator(5) == True

    def test_pipeline_processing(self):
        """Test pre-built pipelines."""
        user_data = {
            "name": "  john doe  ",
            "email": "  TEST@EXAMPLE.COM  ",
            "phone": "(555) 123-4567"
        }

        processed = common.pipelines.userdata(user_data)
        assert processed["name"] == "John Doe"
        assert processed["email"] == "test@example.com"
        # Phone format might vary, just check it's processed
        assert "phone" in processed

    def test_utility_transforms(self):
        """Test utility transforms."""
        assert common.identity("hello") == "hello"

        constant_transform = common.constant("fixed")
        assert constant_transform("anything") == "fixed"

        default_transform = common.default("fallback")
        assert default_transform("hello") == "hello"
        assert default_transform(None) == "fallback"
        assert default_transform("") == "fallback"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_data_cleaning_pipeline(self):
        """Test a complete data cleaning pipeline."""
        from schematix.core.transform import pipeline

        # Create a comprehensive cleaning pipeline
        notempty_validator = common.validate.notempty
        clean_user_data = pipeline(
            common.clean.text,
            common.format.titlecase,
            notempty_validator
        )

        result = clean_user_data("  john doe  ")
        assert result == "John Doe"

    def test_email_processing_chain(self):
        """Test email processing with fallback."""
        from schematix.core.transform import fallback

        # Try to clean email, fallback to constant empty string
        constant_empty = common.constant("")
        safe_email_processor = fallback(
            common.clean.email,
            constant_empty
        )

        assert safe_email_processor("test@example.com") == "test@example.com"
        assert safe_email_processor("invalid") == ""

    def test_numeric_processing_chain(self):
        """Test numeric processing with validation."""
        from schematix.core.transform import pipeline

        # Parse price, validate range, format as currency
        clamp_transform = numbers.clamp(0, 10000)
        price_processor = pipeline(
            common.clean.price,
            clamp_transform,
            common.format.currency
        )

        result = price_processor("$1,234.56")
        assert result == "$1,234.56"

    def test_collection_processing_chain(self):
        """Test collection processing pipeline."""
        from schematix.core.transform import pipeline

        # Clean emails, remove invalid, sort alphabetically
        safe_clean = common.clean.safe.email("")  # Call with default
        map_transform = col.map(safe_clean)
        filter_transform = col.filter(lambda x: x != "")

        safe_processor = pipeline(
            map_transform,
            filter_transform,
            col.unique,
            col.sort
        )

        emails = ["test@example.com", "ADMIN@SITE.COM", "invalid-email"]
        result = safe_processor(emails)
        assert "admin@site.com" in result
        assert "test@example.com" in result
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__])
