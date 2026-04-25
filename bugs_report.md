
# Potential Error-Triggering Cases Report

## Overview

This document summarizes the error-triggering cases observed during our main experiments of HiREST.

## Summary

We collected `6129` HTTP 500 error cases during the main evaluation of HiREST. To avoid inflating the number of failures, we first deduplicated the raw cases using a request-response signature, where two cases are considered the same if they share the same API endpoint, status code, normalized response message, and exception/stack-trace signature when available.

After deduplication, we obtained `4923` unique failure-triggering cases. We then manually inspected these cases together with the corresponding service logs and grouped repeated manifestations with the same root cause into representative robustness bug categories.

The table below summarizes the collected and inspected failures.

| Metric | Value |
|---|---:|
| Total collected HTTP 500 cases | `6129` |
| Unique failure-triggering cases after request-response deduplication | `4923` |
| Subject systems with failures | `7` |
| Manual inspection evidence | Triggering request, observed response, and service log when available |
| Deduplication strategy | Unique request-response signature |
| Grouping strategy | Manual root-cause grouping based on response and service logs |
| Representative robustness cases | 12 |

We identified 12 major cases of robustness issues caused by invalid input values, malformed request metadata, or invalid input combinations introduced by HiREST. 

| id | classification | REST System | Endpoint | Method | 
|---|---|---|---|---:|
| E01 | Unhandled invalid grammer rule | LanguageTool | /check | POST | 
| E02 | Unhandled invalid MongoDB ObjectId | Person Controller | /api/person/{id} | GET | 
| E03 | Invalid type validation failure | Person Controller | /api/persons | POST |
| E04 | Empty-state handling failure | Person Controller | /api/persons/averageAge | GET
| E05 | Invalid type validation failure | Person Controller | /api/person | PUT
| E06 | Invalid country code | REST Countries | /v2/alpha/{alphacode} | GET
| E07 | Persistence-layer validation | News Service | /news | POST
| E08 | Persistence-layer validation | News Service | /news | POST
| E09 | Unknown Entrez Gene ID | Genome Nexus | /ensembl/canonical-gene/entrez/{entrezGeneId} | GET
| E10 | Unresolved HUGO symbol placeholder | Genome Nexus | /ensembl/canonical-gene/hgnc/{hugoSymbol} | GET 
| E11 |  Missing required field | User Management | /users/register | POST
| E12 | Error-handling bug in assignment lookup | Project Tracking System | /app/api/assignments/{employeeId}/{managerId} | GET
| E13 | Encoded percent in request path |  Project Tracking System | /app/api/credentials/{credential} | GET




## LanguageTool `POST /check`
### **ERROR \# E01** :  Empty category id in `disabledCategories`  `"GRAMMAR,,STYLE"` riggers HTTP 500 

**Category.** Potential unhandled invalid input / robustness bug.

**Interpretation.**  The empty category ID is invalid input. However, since the invalid value is supplied by the client through a request parameter `"GRAMMAR,,STYLE"`, the server should ideally reject it with a 4xx response such as `400 Bad Request`, rather than returning `500 Internal Server Error`.

**Send**
```
{
    "rendered_url": "http://localhost:49981/v2/check",
    "header": {"Content-Type": "application/x-www-form-urlencoded"}, 
    "body": {"text": "안녕하세요 세계", "language": "nl", "disabledRules": "UPPERCASE_SENTENCE_START", "enabledCategories": "GRAMMAR,STYLE", "disabledCategories": "GRAMMAR,,STYLE", "enabledOnly": "false"
    }
}
```
**Response**
```
{
    "status_code": 500, 
    "text": "Error: Internal Error: Category id must not be empty: ''", 
    "headers": {"Date": "Tue, 21 Apr 2026 06:02:56 GMT", "Access-control-allow-origin": "*", "Content-length": "56"}
}
```



**Observed behavior.**  
A request to `POST /v2/check` with `disabledCategories="TYPOS, ,GRAMMAR"` returns HTTP 500 with the message:

`Category id must not be empty: ' '`

**Source code details.**
```java
// languagetool/languagetool-core/src/main/java/org/languagetool/rules/CategoryId.java
  public CategoryId(String id) {
    Objects.requireNonNull(id, "Category id must not be null.");
    if (id.trim().isEmpty()) {
      throw new IllegalArgumentException("Category id must not be empty: '" + id + "'");
    }
    this.id = id;
  }
```



## Person Controller `GET /api/person/{id}`
### **ERROR \# E02** Invalid person id triggers MongoDB ObjectId parsing exception

**Category.** Invalid path parameter causing MongoDB ObjectId parsing exception.


**Interpretation.** 
The service appears to directly convert the path parameter into an ObjectId without validating its format first. As a result, the invalid client input causes an uncaught server-side exception and the service returns `500 Internal Server Error`.A more robust behavior would be to reject the request with a client-side error, such as `400 Bad Request` for an invalid identifier format or `404 Not Found` if the identifier is treated as a non-existing resource.



**Send**
```
{
    "rendered_url": "http://localhost:50111/api/person/alpha.beta",
    "header": {"Content-Type": "*/*"}, 
    "body": {}
}
```
**Response**
```
{
  "status_code": 500,
  "text": "{\"cause\":null,\"stackTrace\":[{\"methodName\":\"parseHexString\",\"fileName\":\"ObjectId.java\",\"lineNumber\":363,\"className\":\"org.bson.types.ObjectId\"},{\"methodName\":\"<init>\",\"fileName\":\"ObjectId.java\",\"lineNumber\":190,\"className\":\"org.bson.types.ObjectId\"},{\"methodName\":\"delete\",\"fileName\":\"MongoDBPersonRepository.java\",\"lineNumber\":95,\"className\":\"com.mongodb.starter.repositories.MongoDBPersonRepository\"},{\"methodName\":\"deletePerson\",\"fileName\":\"PersonController.java\",\"lineNumber\":64,\"className\":\"com.mongodb.starter.controllers.PersonController\"}],\"message\":\"invalid hexadecimal representation of an ObjectId: [alpha.beta]\",\"localizedMessage\":\"invalid hexadecimal representation of an ObjectId: [alpha.beta]\"}",
  "headers": {
    "Content-Disposition": "inline;filename=f.txt",
    "Content-Type": "application/json",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 05:29:29 GMT",
    "Connection": "close"
  }
}
```





## Person Controller `POST /api/persons`

### **ERROR \# E03** Invalid request-body field `address.number` format causes deserialization failure

**Category.** Invalid request-body field format causing an unhandled deserialization exception.

**Interpretation.**
The request body is valid JSON and follows the expected top-level structure of the endpoint, but the nested field `address.number` contains the value `"1000.0"`, which is not a valid integer.
The backend model expects this field to be deserialized as an `int`, and Jackson raises an `InvalidFormatException` when attempting to parse the string value `"1000.0"`.


**Send**
```
{
  "rendered_url": "http://localhost:50111/api/persons",
  "header": {
    "Content-Type": "application/json"
  },
  "body": [
    {
      "address": {
        "city": "Coeur d'Alene",
        "country": "USA",
        "number": "1000.0",
        "postcode": "75008",
        "street": "Calle 8"
      },
      "age": "1000",
      "cars": [
        {
          "brand": "O'Neill Motors",
          "maxSpeedKmH": "350.5"
        }
      ]
    }
  ]
}
```
**Response**
```
{
  "status_code": 500,
  "text": {
    "cause": {
      "className": "com.fasterxml.jackson.databind.exc.InvalidFormatException",
      "value": "1000.0",
      "targetType": "int",
      "pathReference": "java.util.ArrayList[0]->com.mongodb.starter.models.Person[\"address\"]->com.mongodb.starter.models.Address[\"number\"]",
      "originalMessage": "Cannot deserialize value of type `int` from String \"1000.0\": not a valid Integer value"
    },
    "timestamp": "2026-04-21T05:30:35.423+00:00",
    "status": 500,
    "error": "Internal Server Error",
    "path": "/api/persons"
  },
  "headers": {
    "Content-Type": "application/json",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 05:30:35 GMT",
    "Connection": "close"
  }
}
```

## Person Controller `GET /api/persons/averageAge`

### **ERROR \# E04** Invalid request-body field `address.number` format causes deserialization failure

**Category.** Empty-state handling failure.

**Interpretation.**
The endpoint computes the average age of stored persons, but the aggregation query appears to return no result, because no matching person records are available in database.


**Send**
```json
{
  "rendered_url":"http://localhost:50111/api/persons/averageAge",
  // There is no person object created in database

    "header": {
    "Content-Type": "*/*"
    },
    "body": {}
}
```

**Response**
```
{
  "status_code": 500,
  "text": {
    "exception": "NullPointerException",
    "message": "Cannot invoke \"com.mongodb.starter.dtos.AverageAgeDTO.getAverageAge()\" because the return value of \"com.mongodb.client.AggregateIterable.first()\" is null",
    "top_application_frames": [
      "com.mongodb.starter.repositories.MongoDBPersonRepository.getAverageAge(MongoDBPersonRepository.java:135)",
      "com.mongodb.starter.controllers.PersonController.averageAge(PersonController.java:90)"
    ]
  },
  "headers": {
    "Content-Type": "application/json",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 05:29:29 GMT",
    "Connection": "close"
  }
}
```


## Person Controller `PUT /api/person`

### **ERROR \# E05** Invalid request-body field `maxSpeedKmH` format causes deserialization failure

**Category.** Invalid request-body field format causing an unhandled deserialization exception.

**Interpretation.**
The request body is valid JSON and follows the expected top-level structure of the endpoint, but the nested field `cars[0].maxSpeedKmH` contains the value `"None"`, which is not a valid float number.
The backend model expects this field to be deserialized as an `float`, and Jackson raises an `InvalidFormatException` when attempting to parse the string value `"None"`.

**Send**
```json
{
  "rendered_url": "http://localhost:50111/api/person",
  "header": {
    "Content-Type": "application/json"
  },
  "body": {
    "address": {
      "city": "Los Angeles",
      "number": "101",
      "street": "Baker Street"
    },
    "age": "-2147483648",
    "cars": [
      {
        "brand": "Ford",
        "maxSpeedKmH": "None",
        "model": "RX-8"
      }
    ],
    "firstName": "Eve",
    "id": {
      "timestamp": "2147483647"
    },
    "insurance": "True",
    "lastName": "van der Meer"
  }
}
```
**Response**
```json
{
  "status_code": 500,
  "text": {
    "cause": {
      "className": "com.fasterxml.jackson.databind.exc.InvalidFormatException",
      "value": "None",
      "targetType": "float",
      "pathReference": "com.mongodb.starter.models.Person[\"cars\"]->java.util.ArrayList[0]->com.mongodb.starter.models.Car[\"maxSpeedKmH\"]",
      "originalMessage": "Cannot deserialize value of type `float` from String \"None\": not a valid Float value"
    },
    "timestamp": "2026-04-21T05:30:35.423+00:00",
    "status": 500,
    "error": "Internal Server Error",
    "path": "/api/person"
  },
  "headers": {
    "Content-Type": "application/json",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 05:30:35 GMT",
    "Connection": "close"
  }
}
```

## REST Countries `GET /v2/alpha/{alphacode}`

### **ERROR \# E06** Empty item in comma-separated query parameter causing error.

**Category.** Empty item in comma-separated query parameter causing server-side error.

**Interpretation.** Although query parameter `codes=,,` is syntactically valid as a comma-separated query string with empty element, it is semantically invalid as a list of country codes.

**Send**
```json
{
  "rendered_url": "http://localhost:50106/rest/v2/alpha?codes=,,&fields=name;capital",
  "header": {
    "Content-Type": "*/*"
  },
  "body": {}
}
```
**Response**
```json
{
  "status_code": 500,
  "text": {
    "status": 500,
    "message": "Internal Server Error"
  },
  "headers": {
    "Content-Type": "application/json;charset=utf-8",
    "Content-Length": "48",
    "Date": "Tue, 21 Apr 2026 06:11:36 GMT",
    "Connection": "close"
  }
}
```

## News Service `POST /news`

### **ERROR # E07: Invalid `authorId` and `country`  cause unhandled JPA validation failure**

**Category.** Invalid request body causing unhandled persistence-layer validation failure.

**Interpretation.** The `authorId` value `6f1d2c3b-4a5e-8c9d-0b1a-2c3d4e5f6a7b` is a UUID-style string with length 36, exceeding the maximum allowed length of 32. The `country` value `NOR` also violates the service's country validation rule. The invalid entity reaches the persistence layer. During transaction commit, Bean Validation detects the constraint violations, Hibernate fails the managed flush, and Spring reports a TransactionSystemException caused by a JPA rollback. The API then returns 500 Internal Server Error.

**Send**

```json
{
  "rendered_url": "http://localhost:50103/news",
  "method": "POST",
  "header": {
    "Content-Type": "application/json;charset=utf-8"
  },
  "body": {
    "authorId": "6f1d2c3b-4a5e-8c9d-0b1a-2c3d4e5f6a7b",
    "country": "NOR",
    "text": "Breaking: Market rally today."
  }
}
```

**Response**
```json
**Response**
```json
{
  "status_code": 500,
  "text": {
    "timestamp": "2026-04-21T05:33:51.750+0000",
    "status": 500,
    "error": "Internal Server Error",
    "message": "Could not commit JPA transaction; nested exception is javax.persistence.RollbackException: Error while committing the transaction",
    "path": "/news"
  },
  "headers": {
    "Content-Type": "application/vnd.tsdes.news+json; version=2;charset=UTF-8",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 05:33:51 GMT",
    "Connection": "close"
  }
}
```

### **ERROR # E08: Blank `authorId` in `POST /news` causes unhandled JPA validation failure**

**Category.** Invalid request body causing unhandled persistence-layer validation failure.


**Interpretation.** The triggering request follows the expected JSON structure, but the authorId field contains only whitespace `"     "`.The invalid entity reaches the JPA persistence layer. During managed flush, Bean Validation detects the constraint violation, the transaction is rolled back, and the API returns 500 Internal Server Error.


**Send**
```json
{
  "rendered_url": "http://localhost:50103/news",
  "method": "POST",
  "header": {
    "Content-Type": "application/json;charset=utf-8"
  },
  "body": {
    "authorId": "   ",
    "country": "Brazil",
    "text": "Startup secures seed funding to accelerate product development."
  }
}
```

**Response**
```json
{
  "status_code": 500,
  "text": {
    "timestamp": "2026-04-21T06:33:38.941+0000",
    "status": 500,
    "error": "Internal Server Error",
    "message": "Could not commit JPA transaction; nested exception is javax.persistence.RollbackException: Error while committing the transaction",
    "path": "/news"
  },
  "headers": {
    "Content-Type": "application/vnd.tsdes.news+json; version=2;charset=UTF-8",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 06:33:38 GMT",
    "Connection": "close"
  }
}
```

## Genome Nexus `GET /ensembl/canonical-gene/entrez/{entrezGeneId}`

### **ERROR # E09: Unknown Entrez Gene ID exception**

**Category.** Unknown Entrez Gene ID exception with frontend fallback response.

**Interpretation.**  the service cannot find a canonical Ensembl gene ID for the provided Entrez Gene ID. This condition should be mapped to a structured API response, such as `404 Not Found`. Instead, the exception propagates as a `500 server error`, and the observed response body is an HTML frontend application shell.

**Send**
```json
{
  "rendered_url": "http://localhost:50110/ensembl/canonical-gene/entrez/7",
  "header": {
    "Content-Type": "*/*"
  },
  "body": {}
}
```

**Response**
```Json
{
  "status_code": 500,
  "text": {
    "contentType": "text/html;charset=UTF-8",
    "title": "Genome Nexus",
    "bodyExcerpt": "<!doctype html><html lang=\"en\"><head>...<title>Genome Nexus</title>...</head><body><noscript>You need to enable JavaScript to run this app.</noscript><div id=\"root\"></div>...</body></html>"
  },
  "headers": {
    "Content-Type": "text/html;charset=UTF-8",
    "Content-Language": "en-US",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 07:08:33 GMT",
    "Connection": "close"
  }
}
```

## Genome Nexus `GET /ensembl/canonical-gene/hgnc/{hugoSymbol}`

### **ERROR # E10: Unresolved HUGO symbol placeholder**

**Category.** Unescaped path parameter hugoSymbol used in regex query / API error handling failure.

**Interpretation.** The placeholder string`{hugoSymbol}` is sent literally as the path parameter.The backend appears to use the path parameter to construct a regular expression for a MongoDB query. When the literal value `{hugoSymbol}` is embedded into the regex pattern `^{hugoSymbol}$`, Java treats {...} as repetition syntax and raises a PatternSyntaxException.

**Send**
```json
{
  "rendered_url": "http://localhost:50110/ensembl/canonical-gene/hgnc/{hugoSymbol}",
  "header": {
    "Content-Type": "*/*"
  },
  "body": {}
}
```

**Response**
```json
{
  "status_code": 500,
  "text": {
    "contentType": "text/html;charset=UTF-8",
    "title": "Genome Nexus",
    "bodyExcerpt": "<!doctype html><html lang=\"en\"><head>...<title>Genome Nexus</title>...</head><body><noscript>You need to enable JavaScript to run this app.</noscript><div id=\"root\"></div>...</body></html>"
  },
  "headers": {
    "Content-Type": "text/html;charset=UTF-8",
    "Content-Language": "en-US",
    "Transfer-Encoding": "chunked"
  }
}
```

## User Management `POST /users/register`

### **ERROR # E11: Missing required body field `name`**

**Category.** Missing required request-body field.

**Interpretation.** the service appears to require a non-null name field. When name is missing, the server does not reject the request at the API boundary with a validation response. Instead, the missing field propagates into the application logic and causes an internal error with the message Name is null. A robust implementation should return a client-side error such as 400 Bad Request, together with a clear validation message indicating that name is required.

**Send**
```json
{
  "rendered_url": "http://localhost:50115/users/register",
  "header": {
    "Content-Type": "application/json"
  },
  "body": {
    "email": "team+alerts@service.io",
    "password": "Sunset#2026!",
    "username": "stefania"
  }
}
```

**Response**
```json
{
  "status_code": 500,
  "text": {
    "timestamp": "2026-04-21T06:50:21.844+0000",
    "status": 500,
    "error": "Internal Server Error",
    "message": "Name is null",
    "path": "/users/register"
  },
  "headers": {
    "Content-Type": "application/json",
    "Transfer-Encoding": "chunked",
    "Date": "Tue, 21 Apr 2026 06:50:21 GMT",
    "Connection": "close"
  }
}
```


## Project Tracking System `GET /app/api/assignments/{employeeId}/{managerId}`

### **ERROR # E12: Null HTTP status in assignment lookup response**

**Category.** Assignment lookup error-handling failure.

**Interpretation.** The two path parameters are syntactically valid numeric values and appear to represent an employee identifier and a manager identifier. However, this uncommon or **invalid identifier combination** triggers an error-handling path in the controller. While constructing the response, the controller **passes a null HTTP status to Spring's ResponseEntity**. Since Spring requires a concrete status code, such as 200 OK, 400 Bad Request, or 404 Not Found, it throws IllegalArgumentException: HttpStatus must not be null.


**Send**
```json
{
  "rendered_url": "http://localhost:50118/app/api/assignments/256/1999999999",
  "header": {
    "Content-Type": "*/*"
  },
  "body": {}
}
```

**Response**
```json
{
  "status_code": 500,
  "text": {
    "contentType": "text/html;charset=UTF-8",
    "title": "Gateway error",
    "bodyExcerpt": "<!DOCTYPE html><html><head><title>Gateway error</title>...</head><body>...<h1>Error 500, Gateway error!</h1>...</body></html>"
  },
  "headers": {
    "Content-Type": "text/html;charset=UTF-8",
    "Content-Language": "en-US",
    "Transfer-Encoding": "chunked"
  }
}
```

## Project Tracking System `GET /app/api/credentials/{credential}`

### **ERROR # E12: Encoded percent in request path parameter `credential`**

**Category.** Encoded percent in request path parameter causing firewall rejection.

**Interpretation.** The path value `x%25y` contains `%25`, the percent-encoded representation of %. Spring Security's StrictHttpFirewall treats this URL pattern as potentially malicious and rejects the request before it reaches the application controller. The reliability issue is that the rejected client request is ultimately mapped to 500 Internal Server Error and rendered as an HTML Gateway error page. Since the failure is caused by a malformed or rejected client-supplied URL, the application should return a client-side error such as ``400 Bad Request`` or `403 Forbidden`, preferably with a structured API error response.

**Send**

```json
{
  "rendered_url": "http://localhost:50118/app/api/credentials/x%25y",
  "method": "GET",
  "header": {
    "Content-Type": "*/*"
  },
  "body": {}
}
```

**Response**
```json
{
  "status_code": 500,
  "text": {
    "contentType": "text/html;charset=UTF-8",
    "title": "Gateway error",
    "bodyExcerpt": "<!DOCTYPE html><html><head><title>Gateway error</title>...</head><body>...<h1>Error 500, Gateway error!</h1>...</body></html>"
  },
  "headers": {
    "Content-Type": "text/html;charset=UTF-8",
    "Content-Language": "en-US",
    "Transfer-Encoding": "chunked"
  }
}
```


