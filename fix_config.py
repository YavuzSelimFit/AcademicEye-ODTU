import os

# Target path that auto_init used
config_path = r"C:\Users\Yavuz\.config\pybliometrics.cfg"

# Ensure dir exists
os.makedirs(os.path.dirname(config_path), exist_ok=True)

content = """[Directories]
AbstractRetrieval = C:\\Users\\Yavuz\\.scopus\\Scopus\\abstract_retrieval 
AffiliationRetrieval = C:\\Users\\Yavuz\\.scopus\\Scopus\\affiliation_retrieval
AffiliationSearch = C:\\Users\\Yavuz\\.scopus\\Scopus\\affiliation_search 
AuthorRetrieval = C:\\Users\\Yavuz\\.scopus\\Scopus\\author_retrieval     
AuthorSearch = C:\\Users\\Yavuz\\.scopus\\Scopus\\author_search
ArticleEntitlement = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\article_entitlement
ArticleMetadata = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\article_metadata
ArticleRetrieval = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\article_retrieval
NonserialTitle = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\nonserial_title
CitationOverview = C:\\Users\\Yavuz\\.scopus\\Scopus\\citation_overview   
ObjectMetadata = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\object_metadata
ObjectRetrieval = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\object_retrieval
PlumXMetrics = C:\\Users\\Yavuz\\.scopus\\Scopus\\plumx
PublicationLookup = C:\\Users\\Yavuz\\.scopus\\Scival\\publication_lookup 
AuthorMetrics = C:\\Users\\Yavuz\\.scopus\\Scival\\author_metrics
InstitutionLookupMetrics = C:\\Users\\Yavuz\\.scopus\\Scival\\institution_metrics
TopicLookupMetrics = C:\\Users\\Yavuz\\.scopus\\Scival\\topic_metrics     
ScDirSubjectClassifications = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\subject_classification   
ScienceDirectSearch = C:\\Users\\Yavuz\\.scopus\\ScienceDirect\\science_direct_search
ScopusSearch = C:\\Users\\Yavuz\\.scopus\\Scopus\\scopus_search
SerialTitleSearch = C:\\Users\\Yavuz\\.scopus\\Scopus\\serial_search      
SerialTitleISSN = C:\\Users\\Yavuz\\.scopus\\Scopus\\serial_title
SubjectClassifications = C:\\Users\\Yavuz\\.scopus\\Scopus\\subject_classification

[Authentication]
APIKey = 1eadcb2954e012a0481889a8aa9a0aff

[Requests]
Timeout = 20
Retries = 5
"""

with open(config_path, "w", encoding="utf-8") as f:
    f.write(content)
    
print(f"✅ Clean config written to {config_path}")
