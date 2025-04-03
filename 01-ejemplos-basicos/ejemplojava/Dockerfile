FROM maven:3.8.3-openjdk-17 as builder

# Copiar el código local al contenedor de la imagen
COPY pom.xml .
COPY src ./src

# Hago el build
RUN mvn package -DskipTests

FROM openjdk:17-jdk-bullseye

COPY --from=builder /target/ejemplo-*.jar /ejemplo.jar

CMD ["java", "-jar", "/ejemplo.jar"]