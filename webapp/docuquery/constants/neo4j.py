URL = "bolt://neo4j:7687"
USERNAME = "neo4j"
PASSWORD = "root@neo4j"
EMBEDDING_NODE_LABEL = "Embeddable"
EMBEDDING_NODE_PROPERTY = "embedding"
common_columns = [
    "id",
    "text",
    "title",
]

disease_columns = [
    "alt_code",
    "alt_name",
    "description",
    "disease_code",
    "disease_name",
]

fundingopportunity_columns = [
    "id",
    "name",
    "type",
    "sponsor",
    "goal",
    "term",
    "eligibility_criteria",
]

consortium_columns = [
    "name",
    "description",
    "code",
    "activation_date",
    "deactivation_date",
    "funding_statement",
    "grant_number",
    "contact_registry_label",
    "display_acronym"
]

diseasecategory_columns =[
    "name"
]

publication_columns = [
    "title",
    "first_author",
    "authors",
    "citation",
    "pub_date_year",
    "pub_date_month",
    "pub_date_day",
    "journal_book",
    "pmid",
    "pmcid",
    "doi",
    "nihmsid",
    "website_url",
    "summary",
]

study_columns = ["id", "name", "protocol"]
complion_record_columns = ["id", "name"]
enrollment_status_columns = ["id", "name"]
irb_approval_status_columns = ["id", "name"]
research_type_columns = ["id", "name"]
study_type_columns = ["id", "name"]
treatment_tested_columns = ["id", "name"]

sites_columns = ["id", "code", "name"]

pag_columns = [
    'id',
    'name',
    'code',
    'description',
    'alt_name',
    'website_url',
    'logo_url',
    'status_id'
]

gard_columns = [
    'id',
    'gard_id',
    'name'
]

contact_columns = [
    "id",
    "first_name",
    "last_name",
    "post_nominals",
    "title",
    "phone",
    "email",
    "address",
    "city",
    "state",
    "country",
    "zipcode",
    "status_id"
]


EMBEDDABLE_NODE_PROPERTIES = list(
    set(
        common_columns +
        disease_columns +
        fundingopportunity_columns +
        consortium_columns +
        publication_columns +
        study_columns +
        pag_columns +
        gard_columns +
        contact_columns
    )
)