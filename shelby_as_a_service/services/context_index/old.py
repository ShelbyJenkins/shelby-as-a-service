@classmethod
def get_requested_domain(cls, requested_domain_name: str):
    if requested_domain_name not in cls.list_of_data_domain_ui_names:
        raise Exception(f"Data domain name {requested_domain_name} does not exist")
    cls.current_domain = DataDomain(
        domain_config=cls.index_config.data_domains[requested_domain_name]
    )
    cls.index_config.current_domain_name = requested_domain_name


@classmethod
def get_requested_source(cls, requested_source_name: str):
    if requested_source_name not in cls.current_domain.list_of_data_source_ui_names:
        raise Exception(f"Data source name {requested_source_name} does not exist")
    cls.current_domain.current_source = DataSource(
        source_config=cls.current_domain.domain_config.data_sources[requested_source_name]
    )
    cls.current_domain.domain_config.current_source_name = requested_source_name


@classmethod
def create_data_domain(
    cls,
    domain_name: Optional[str] = None,
    description: Optional[str] = None,
    batch_update_enabled: bool = True,
):
    if not description:
        description = DataDomain.ClassConfigModel.model_fields["description"].default
    if not domain_name:
        domain_name = DataDomain.ClassConfigModel.model_fields["name"].default
    counter = 1
    while domain_name in cls.list_of_data_domain_ui_names:
        domain_name = f"{domain_name}_{counter}"
        counter += 1
    if not domain_name:
        raise Exception("Data domain name cannot be None")
    cls.index_config.data_domains[domain_name] = DataDomain.ClassConfigModel(
        name=domain_name,
        description=description,
        database_provider=database_provider
        if database_provider is not None
        else cls.index_config.database_provider,
        doc_loading_provider=doc_loading_provider
        if doc_loading_provider is not None
        else cls.index_config.doc_loading_provider,
        batch_update_enabled=batch_update_enabled,
    )
    cls.list_of_data_domain_ui_names.append(domain_name)
    cls.index_config.current_domain_name = domain_name


@classmethod
def create_data_source(
    cls,
    data_domain: "DataDomain",
    source_name: Optional[str] = None,
    description: Optional[str] = None,
    batch_update_enabled: bool = True,
):
    if data_domain.domain_config.name not in cls.list_of_data_domain_ui_names:
        raise Exception(f"Data domain {data_domain.domain_config.name} does not exist")
    if not description:
        description = DataSource.ClassConfigModel.model_fields["description"].default
    if not source_name:
        source_name = DataSource.ClassConfigModel.model_fields["name"].default
    counter = 1
    while source_name in data_domain.list_of_data_source_ui_names:
        source_name = f"{source_name}_{counter}"
        counter += 1
    if not source_name:
        raise Exception("Data source name cannot be None")
    data_domain.domain_config.data_sources[source_name] = DataSource.ClassConfigModel(
        name=source_name,
        description=description,
        database_provider=database_provider
        if database_provider is not None
        else data_domain.domain_config.database_provider,
        doc_loading_provider=doc_loading_provider
        if doc_loading_provider is not None
        else data_domain.domain_config.doc_loading_provider,
        batch_update_enabled=batch_update_enabled,
    )
    data_domain.list_of_data_source_ui_names.append(source_name)
    data_domain.domain_config.current_source_name = source_name
