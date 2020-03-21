SELECT C.CustomerId,
       C.FirstName,
       C.LastName,
       count(I.CustomerID) AS "Purchase count",
       sum(I.Total) AS "Total Spent"
FROM invoices AS I
INNER JOIN customers AS C ON I.CustomerId = C.CustomerId
GROUP BY I.CustomerId
ORDER BY [Purchase count] DESC,
         [total spent] DESC;

