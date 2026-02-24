# Branch Naming and Commit Guidelines
*Branch and Commit Messages Naming Conventions* 


## Naming Types 

| Type         | Meaning        |
| :----------- | :------------- |
| fix          | Bug fix        |
| feat         | New feature    |
| docs         | Documentation  |
| ci           | CI/CD changes  |
| refactor     | Refactoring    |
| perf         | Performance    |
| style        | Code style     |
| team         | Team-related   |

## Branch Naming Conventions
```bash
git switch -c type/explaining-thing 
```

> [!WARNING] 
> The regex pattern below must be enforced. 
>
> ```regex
> ^[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)*$
> ```

## Commit Message Conventions
```bash
git commit -m "type: explaining briefly what you did"
```
