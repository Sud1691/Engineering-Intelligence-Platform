"""
Data source ingestors for the Living Architecture Map.

Each module here knows how to translate an external signal (CloudTrail,
Terraform state, X-Ray traces, etc.) into service-level dependency
information that can be fed into the architecture graph.
"""

