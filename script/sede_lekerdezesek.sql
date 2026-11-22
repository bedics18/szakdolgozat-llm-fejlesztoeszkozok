-- A) Nem törölt kérdések havonta (Posts tábla)
-- Sávok (Id >= ... AND Id < ...):
--   46000000-50000000, 50000000-54000000, 54000000-58000000,
--   58000000-62000000, 62000000-66000000, 70000000-74000000
SELECT YEAR(CreationDate) AS Ev, MONTH(CreationDate) AS Ho, COUNT(*) AS Kerdesek
FROM Posts
WHERE Id >= 46000000 AND Id < 50000000
  AND PostTypeId = 1
GROUP BY YEAR(CreationDate), MONTH(CreationDate)
ORDER BY Ev, Ho;

-- B) Megmaradt és összes (törölt kérdésekkel együtt) havonta
--    (PostsWithDeleted tábla)
-- Sávok: 66000000-70000000, valamint 74000000 felett (felső határ nélkül)
SELECT YEAR(CreationDate) AS Ev, MONTH(CreationDate) AS Ho,
       SUM(CASE WHEN DeletionDate IS NULL THEN 1 ELSE 0 END) AS Megmaradt,
       COUNT(*) AS Osszes
FROM PostsWithDeleted
WHERE Id >= 74000000
  AND PostTypeId = 1
GROUP BY YEAR(CreationDate), MONTH(CreationDate)
ORDER BY Ev, Ho;
