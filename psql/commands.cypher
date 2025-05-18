LOAD CSV WITH HEADERS FROM 'file:///diseases.csv' AS row
CREATE (:Disease:Postgres:Embeddable {
  disease_name: row.name,
  description: row.description,
  disease_code: row.code,
  alt_name: row.alt_name,
  alt_code: row.alt_code,
  website_url: row.website_url
});


LOAD CSV WITH HEADERS FROM 'file:///funding_opportunities.csv' AS row
WITH row
CREATE (fo:FundingOpportunity:Postgres:Embeddable {
    id: toInteger(row.fundingopportunity_id),
    name: row.fundingopportunity_name,
    type: row.fundingopportunity_type,
    sponsor: row.fundingopportunity_sponsor,
    rfa_url: row.fundingopportunity_rfa_url,
    application_due_date: row.fundingopportunity_application_due_date,
    goal: row.fundingopportunity_goal,
    amount: row.fundingopportunity_amount,
    term: row.fundingopportunity_term,
    eligibility_criteria: row.fundingopportunity_eligibility_criteria,
    loi_due_date: row.fundingopportunity_loi_due_date,
    status_id: toInteger(row.fundingopportunity_status_id),
    rolling_application: row.fundingopportunity_rolling_application,
    priority: toInteger(row.fundingopportunity_priority)
})
CREATE (c:Consortium:Postgres:Embeddable {
    id: toInteger(row.consortium_id),
    name: row.consortium_name,
    description: row.consortium_description,
    code: row.consortium_code,
    website_url: row.consortium_website_url,
    status_id: toInteger(row.consortium_status_id),
    activation_date: row.consortium_activation_date,
    deactivation_date: row.consortium_deactivation_date,
    logo_url: row.consortium_logo_url,
    publications_url: row.consortium_publications_url,
    clinical_sites_url: row.consortium_clinical_sites_url,
    pags_url: row.consortium_pags_url,
    research_studies_url: row.consortium_research_studies_url,
    funding_statement: row.consortium_funding_statement,
    grant_number: row.consortium_grant_number,
    collaborations_url: row.consortium_collaborations_url,
    contact_registry_label: row.consortium_contact_registry_label,
    contact_registry_url: row.consortium_contact_registry_url,
    display_acronym: row.consortium_display_acronym
})
CREATE (d:DiseaseCategory:Postgres:Embeddable {
    id: toInteger(row.diseasecategory_id),
    name: row.diseasecategory_name
})
CREATE (fo)-[:BELONGS_TO]->(c)
CREATE (c)-[:RELATED_TO]->(d);


LOAD CSV WITH HEADERS FROM 'file:///publications.csv' AS row
CREATE (:Publication:Postgres:Embeddable {
    id: row.id,
    title: row.title,
    first_author: row.first_author,
    authors: row.authors,
    citation: row.citation,
    pub_date_year: toInteger(row.pub_date_year),
    pub_date_month: toInteger(row.pub_date_month),
    pub_date_day: toInteger(row.pub_date_day),
    journal_book: row.journal_book,
    pmid: row.pmid,
    pmcid: row.pmcid,
    doi: row.doi,
    nihmsid: row.nihmsid,
    website_url: row.website_url,
    summary: row.summary
});



LOAD CSV WITH HEADERS FROM 'file:///studies.csv' AS row

MERGE (study:Study:Postgres:Embeddable {id: row.study_id})
SET study.name = row.study_name,
    study.protocol = row.study_protocol

MERGE (complionRecord:ComplionRecord:Postgres:Embeddable {id: row.complion_record_id})
SET complionRecord.name = row.complion_record_name

MERGE (enrollmentStatus:EnrollmentStatus:Postgres:Embeddable {id: row.enrollment_status_id})
SET enrollmentStatus.name = row.enrollment_status_name

MERGE (irbApprovalStatus:IRBApprovalStatus:Postgres:Embeddable {id: row.irb_approval_status_id})
SET irbApprovalStatus.name = row.irb_approval_status_name

MERGE (researchType:ResearchType:Postgres:Embeddable {id: row.research_type_id})
SET researchType.name = row.research_type_name

MERGE (studyType:StudyType:Postgres:Embeddable {id: row.study_type_id})
SET studyType.name = row.study_type_name

MERGE (treatmentTested:TreatmentTested:Postgres:Embeddable {id: row.treatment_tested_id})
SET treatmentTested.name = row.treatment_tested_name

MERGE (study)-[:HAS_COMPLION_RECORD]->(complionRecord)
MERGE (study)-[:HAS_ENROLLMENT_STATUS]->(enrollmentStatus)
MERGE (study)-[:HAS_IRB_APPROVAL_STATUS]->(irbApprovalStatus)
MERGE (study)-[:HAS_RESEARCH_TYPE]->(researchType)
MERGE (study)-[:HAS_STUDY_TYPE]->(studyType)
MERGE (study)-[:HAS_TREATMENT_TESTED]->(treatmentTested);



LOAD CSV WITH HEADERS FROM 'file:///pags.csv' AS row
CREATE (:Pag:Postgres:Embeddable {
    id: toInteger(row.id),
    name: row.name,
    code: row.code,
    description: row.description,
    alt_name: row.alt_name,
    website_url: row.website_url,
    logo_url: row.logo_url,
    status_id: toInteger(row.status_id)
});


LOAD CSV WITH HEADERS FROM 'file:///gards.csv' AS row
CREATE (:Gard:Postgres:Embeddable {
    id: toInteger(row.id),
    gard_id: row.gard_id,
    name: row.name
});


LOAD CSV WITH HEADERS FROM 'file:///contacts.csv' AS row
CREATE (c:Contact:Postgres:Embeddable {
    id: toInteger(row.id),
    first_name: row.first_name,
    last_name: row.last_name,
    post_nominals: row.post_nominals,
    title: row.title,
    phone: row.phone,
    email: row.email,
    address: row.address,
    city: row.city,
    state: row.state,
    country: row.country,
    zipcode: row.zipcode,
    status_id: toInteger(row.status_id)
});
