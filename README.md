## Libs postgress
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

## Rule for cluster job

1. items_with_cluster
2. items_without_cluster

3. for each cluster:
      choose the item that will cluster canonical item (temporary: first)

4. compare Splink:
   a) new_items × representatives
   b) new_items × new_items

5. Decision:
   - cluster canonical item  → enter in a known cluster
   - else:
       groups between not clustered products
       crates new cluster for each grupo of products

6. Updates cluster_id

