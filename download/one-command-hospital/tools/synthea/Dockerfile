# Synthea — synthetic patient generator (improvement #5 substrate: zero-PHI testing)
# One-time build is slow (Maven); the jar is cached in the image layer afterwards.
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
RUN git clone --depth 1 https://github.com/synthetichealth/synthea.git .
RUN mvn -q -B package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /work
COPY --from=build /src/target/synthea.jar /app/synthea.jar
# Synthea writes FHIR bundles to /work/output (mounted to ./data/synthea in compose)
ENTRYPOINT ["java", "-jar", "/app/synthea.jar"]
CMD ["-p", "100"]
