import copy
import pkgutil
import json
from jsonschema import (
    Draft7Validator,
    draft7_format_checker,
    ValidationError,
)

# TODO do we need to catch a possible exception here ?
v7data = pkgutil.get_data("jsonschema", "schemas/draft7.json")
v7schema = json.loads(v7data.decode("utf-8"))


class JsonSchema:

    schematype = "jsonchema"

    def __init__(self, schema, filename, root):
        """Initilized a new JsonSchema from a dict

        Args:
            schema (dict): Data representing the schema, must be jsonschema valid
            filename (string): name of the schema file on the filesystem
            root (string): Absolute path to the directory where the schema file is located.
        """
        self.filename = filename
        self.root = root
        self.data = schema
        self.id = self.data.get("$id")
        self.validator = None
        self.strict_validator = None

    def get_id(self):
        """Return the unique ID of the schema."""
        return self.id

    def validate(self, data, strict=False):
        """Validate a given data with this schema.

        Args:
            data (dict, list): Data to validate against the schema
            strict (bool, optional): if True the validation will automatically flag additional properties. Defaults to False.

        Returns:
            Iterator: Iterator of ValidationError
        """
        if strict:
            validator = self.__get_strict_validator()
        else:
            validator = self.__get_validator()

        return validator.iter_errors(data)

    def __get_validator(self):
        """Return the validator for this schema, create if it doesn't exist already.

        Returns:
            Draft7Validator: Validator for this schema 
        """
        if self.validator:
            return self.validator

        self.validator = Draft7Validator(self.data)

        return self.validator

    def __get_strict_validator(self):
        """Return a strict version of the Validator, create it if it doesn't exist already.

        To create strict version of the schema, this function add `additionalProperties` to all objects in the schema
        TODO Currently the function is only modifying the top level object, need to add that to all objects recursively

        Returns:
            Draft7Validator: Validator for this schema in strict mode
        """
        if self.strict_validator:
            return self.strict_validator

        # Create a copy if the schema first and modify it to insert `additionalProperties`
        schema = copy.deepcopy(self.data)

        if schema.get("additionalProperties", False) is not False:
            print(f"{schema['$id']}: Overriding existing additionalProperties: {schema['additionalProperties']}")

        schema["additionalProperties"] = False

        # XXX This should be recursive, e.g. all sub-objects, currently it only goes one level deep, look in jsonschema for utilitiies
        for p, prop in schema.get("properties", {}).items():
            items = prop.get("items", {})
            if items.get("type") == "object":
                if items.get("additionalProperties", False) is not False:
                    print(f"{schema['$id']}: Overriding item {p}.additionalProperties: {items['additionalProperties']}")
                items["additionalProperties"] = False

        self.strict_validator = Draft7Validator(schema)
        return self.strict_validator

    def check_if_valid(self):
        """Check if the schema itself is valid against JasonSchema draft7.
        
        Returns:
            Iterator: Iterator of ValidationError
        """
        validator = Draft7Validator(v7schema)
        return validator.iter_errors(self.data)
