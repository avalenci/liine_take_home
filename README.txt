How to run:
1. docker build --tag python-docker .
2. docker run --publish 5000:5000 python-docker
3. Send GET to localhost:5000/?date=<insert-date>
4. Date must be in "%Y-%m-%d %H:%M:%S.%f" format