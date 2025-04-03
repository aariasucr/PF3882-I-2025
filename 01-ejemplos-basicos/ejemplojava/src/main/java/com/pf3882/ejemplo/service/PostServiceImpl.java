package com.pf3882.ejemplo.service;

import com.pf3882.ejemplo.dto.PostDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.DefaultUriBuilderFactory;
import org.springframework.web.util.UriBuilderFactory;

@Slf4j
@Service
public class PostServiceImpl implements PostService {
  private final RestTemplate restTemplate;
  private final String postServiceBaseUrl;

  public PostServiceImpl(RestTemplate restTemplate,
                         @Value("${pf3882.postServiceBaseUrl}") String postServiceBaseUrl) {
    this.restTemplate = restTemplate;
    this.postServiceBaseUrl = postServiceBaseUrl;
    log.info("Post Service URL: " + postServiceBaseUrl);
  }

  @Override
  public PostDTO getPost(int id) {
    log.info("Estoy en getPost con el id: {}", id);

    // Generamos la URL del servicio que queremos consumir
    UriBuilderFactory factory = new DefaultUriBuilderFactory(this.postServiceBaseUrl);
    var uriBuilder = factory.builder().pathSegment("posts", String.valueOf(id));
    var uri = uriBuilder.build();

    // Creamos los headers para la petición
    HttpHeaders headers = new HttpHeaders();
    headers.add("Content-Type", "application/json");
    headers.add("Accept", "application/json");

    // Definimos el entity que contiene los headers y puede tener el payload (para un POST o PUT)
    HttpEntity<?> entity = new HttpEntity<Object>(headers);


    // Realizamos la petición al servicio externo
    var responseEntity = this.restTemplate.exchange(uri, HttpMethod.GET, entity, PostDTO.class);

    PostDTO resultado = responseEntity.getBody();
    log.info("Resultado: {}", resultado);
    return resultado;


  }
}
