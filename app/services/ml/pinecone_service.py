import pinecone
from app.core.config import settings

class PineconeService:
    def __init__(self, index_name=settings.PINECONE_INDEX_NAME):
        self.pinecone_api_key = settings.PINECONE_API_KEY
        self.pinecone_index_name = index_name
        self.pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pc.Index(self.pinecone_index_name)

    def upsert_pinecone_data(self, vector, id, namespace='', metadata=None):
        try:
            temp_dict = {
                'id': str(id),
                'values': vector
            }

            if metadata:
                temp_dict['metadata'] = metadata

            self.index.upsert(vectors=[temp_dict], namespace=namespace)
        except Exception as e:
            raise Exception(f"An error occurred during Pinecone upsert: {e}")

    def query_pinecone_data(self, vector, namespace="", top_k=3, metadata_filter=None, keyword_filter=None):
        try:
            query_params = {
                "namespace": namespace,
                "top_k": top_k,
                "include_values": True,
                "include_metadata": True,
                "vector": vector
            }
            
            if metadata_filter:
                query_params["filter"] = metadata_filter
            
            response = self.index.query(**query_params)
            
            if keyword_filter:
                filtered_matches = []
                for match in response['matches']:
                    metadata = match.get('metadata', {})
                    if any(keyword in metadata.get('text', '') for keyword in keyword_filter):
                        filtered_matches.append(match)
                response['matches'] = filtered_matches

            return response
        except Exception as e:
            raise Exception(f"An error occurred during Pinecone query: {e}")

    def delete_pinecone_data(self, id, namespace=""):
        try:
            self.index.delete(ids=[str(id)], namespace=namespace)
        except Exception as e:
            raise Exception(f"An error occurred during Pinecone delete: {e}")

    def fetch_all_ids(self, namespace=""):
        try:
            zero_vector = [0] * 3072
            response = self.index.query(vector=zero_vector, top_k=10000, include_metadata=True, include_values=False, namespace=namespace)
            return set(match['id'] for match in response['matches'])
        except Exception as e:
            raise Exception(f"An error occurred during fetching IDs from Pinecone: {e}")

    def hybrid_search(self, vector, namespace="", top_k=3, metadata_filter=None, keyword_filter=None):
        try:
            vector_response = self.query_pinecone_data(vector, namespace, top_k, metadata_filter)

            # If keyword filter is provided, perform an additional search/filter
            if keyword_filter:
                filtered_matches = []
                for match in vector_response['matches']:
                    metadata = match.get('metadata', {})
                    if any(keyword in metadata.get('text', '') for keyword in keyword_filter):
                        filtered_matches.append(match)
                vector_response['matches'] = filtered_matches

            return vector_response
        except Exception as e:
            raise Exception(f"An error occurred during hybrid search: {e}")