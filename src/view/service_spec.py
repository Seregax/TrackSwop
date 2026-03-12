from service_field import ServiceField, FieldType


service_spec = [

    ServiceField(
        name="source_path",
        field_type=FieldType.STRING,
        label="Source path"
    ),

    ServiceField(
        name="destination_path",
        field_type=FieldType.STRING,
        label="Destination path"
    ),

    ServiceField(
        name="overwrite",
        field_type=FieldType.BOOLEAN,
        label="Overwrite files"
    ),

    ServiceField(
        name="max_size",
        field_type=FieldType.NUMBER,
        label="Max file size"
    )
]