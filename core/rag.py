import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

# ============================================================
# CONFIGURATION
# ============================================================

FILE_PATH = "data/AI_Industrial_Maintenance_Knowledge_Base_Final-1.xlsx"
MODEL_NAME = "all-MiniLM-L6-v2"

# ============================================================
# LOAD KNOWLEDGE BASE
# ============================================================

def load_knowledge_base():
    df = pd.read_excel(
        FILE_PATH,
        sheet_name="Knowledge Base"
    )

    df = df.fillna("")

    return df

# ============================================================
# CONVERT KNOWLEDGE BASE RECORDS INTO SEARCHABLE TEXT
# ============================================================

def create_documents(df):

    documents = []

    for _, row in df.iterrows():

        document = f"""
Machine: {row.get('Machine', '')}

Fault / Incident: {row.get('Fault / Incident', '')}

Severity: {row.get('Severity', '')}

Symptoms: {row.get('Symptoms', '')}

Possible Causes: {row.get('Possible Causes', '')}

Diagnostic Questions: {row.get('Diagnostic Questions', '')}

Checks / Evidence: {row.get('Checks / Evidence', '')}

Troubleshooting Guidance: {row.get('Troubleshooting Guidance', '')}

Safety / Stop Condition: {row.get('Safety / Stop Condition', '')}

Escalation: {row.get('Escalation', '')}

Keywords / Tags: {row.get('Keywords / Tags', '')}
"""

        documents.append(document.strip())

    return documents

# ============================================================
# CREATE VECTOR INDEX
# ============================================================

def create_vector_index(documents):

    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return model, index

# ============================================================
# SEARCH KNOWLEDGE BASE
# ============================================================

def search_knowledge_base(
    query,
    documents,
    model,
    index,
    top_k=3
):

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx < len(documents):

            results.append({
                "score": float(score),
                "document": documents[idx]
            })

    return results

# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("\nLoading Knowledge Base...")

    df = load_knowledge_base()

    print(f"Knowledge Base records: {len(df)}")

    documents = create_documents(df)

    print("Creating vector index...")

    model, index = create_vector_index(documents)

    print("RAG system ready!")

    print("\n--------------------------------")
    print("TEST SEARCH")
    print("--------------------------------")

    query = "The industrial motor is overheating and vibrating."

    results = search_knowledge_base(
        query,
        documents,
        model,
        index,
        top_k=3
    )

    print(f"\nQuery: {query}\n")

    for i, result in enumerate(results, start=1):

        print(f"\nRESULT {i}")
        print(f"Similarity Score: {result['score']:.3f}")
        print(result["document"])
        print("--------------------------------")
