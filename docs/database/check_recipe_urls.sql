-- 레시피 테이블에 URL이 있는지 확인
SELECT 
    COUNT(*) as total_recipes,
    COUNT(url) as recipes_with_url,
    COUNT(*) - COUNT(url) as recipes_without_url,
    ROUND(COUNT(url)::numeric / COUNT(*)::numeric * 100, 2) as url_percentage
FROM recipe_blob_emb;

-- URL이 있는 레시피 샘플 10개
SELECT 
    id,
    title,
    url,
    LENGTH(url) as url_length
FROM recipe_blob_emb
WHERE url IS NOT NULL
LIMIT 10;

-- URL이 없는 레시피 샘플 10개
SELECT 
    id,
    title,
    url
FROM recipe_blob_emb
WHERE url IS NULL
LIMIT 10;

