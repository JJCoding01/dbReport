SELECT E.EmployeeId,
       E.LastName,
       E.FirstName,
       count(C.CustomerID) AS "customer count"
FROM employees AS E
INNER JOIN customers AS C ON C.SupportRepId = E.EmployeeId
GROUP BY E.EmployeeId
ORDER BY count(C.CustomerID) DESC;

