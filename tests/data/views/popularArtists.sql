SELECT artists.Name AS "artist name",
       count(albums.AlbumId)
FROM artists
INNER JOIN albums ON artists.ArtistId = albums.ArtistId
GROUP BY artists.ArtistId
HAVING count(albums.AlbumId) > 3
ORDER BY count(albums.AlbumId) DESC;
