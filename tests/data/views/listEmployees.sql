SELECT LastName,
       FirstName,
       Title,
       HireDate - BirthDate AS "hire age",
       date('now') - BirthDate AS "current age",
       date('now') - HireDate AS "employment duration"
FROM employees
ORDER BY "HireDate" ASC
