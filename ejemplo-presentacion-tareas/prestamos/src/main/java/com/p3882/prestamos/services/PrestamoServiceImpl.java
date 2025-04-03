package com.p3882.prestamos.services;

import com.p3882.prestamos.dto.LibroDTO;
import com.p3882.prestamos.dto.PrestamoDTO;
import com.p3882.prestamos.dto.PrestamoRequestDTO;
import com.p3882.prestamos.dto.UsuarioDTO;
import com.p3882.prestamos.exception.NotFoundException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Slf4j
@Service
public class PrestamoServiceImpl implements PrestamoService{
  private final RestTemplate restTemplate;
  private final String usuariosServiceBaseUrl;
  private final String librosServiceBaseUrl;
  private final List<PrestamoDTO> prestamos;

  public PrestamoServiceImpl(RestTemplate restTemplate,
                             @Value("${pf3882.usuariosServiceBaseUrl}") String usuariosServiceBaseUrl,
                             @Value("${pf3882.librosServiceBaseUrl}") String librosServiceBaseUrl) {
    this.restTemplate = restTemplate;
    this.usuariosServiceBaseUrl = usuariosServiceBaseUrl;
    this.librosServiceBaseUrl = librosServiceBaseUrl;
    this.prestamos = new ArrayList<>();
  }

  @Override
  public List<PrestamoDTO> getPrestamos(){
    return this.prestamos;
  }

  @Override
  public PrestamoDTO getPrestamo(int id) {
    for (PrestamoDTO prestamo : prestamos) {
      if (prestamo.getId() == id) {
        return prestamo;
      }
    }
    return null;
  }

  @Override
  public PrestamoDTO addPrestamo(PrestamoRequestDTO prestamoRequestDTO) {
    UsuarioDTO usuarioDTO = this.getUsuario(prestamoRequestDTO.getUsuarioId());
    if (usuarioDTO == null) {
      log.error("Usuario no encontrado");
      throw new NotFoundException("Usuario no encontrado");
    }
    LibroDTO libroDTO = this.getLibro(prestamoRequestDTO.getLibroId());
    if (libroDTO == null) {
      log.error("Libro no encontrado");
      throw new NotFoundException("Libro no encontrado");
    }
    PrestamoDTO prestamoDTO = new PrestamoDTO();
    Date hoy = new Date();
    Date fechaDevolucion = new Date(hoy.getTime() + (prestamoRequestDTO.getDiasPrestamo() * 24 * 60 * 60 * 1000));
    prestamoDTO.setId(prestamos.size() + 1);
    prestamoDTO.setFechaCreacionPrestamo(hoy);
    prestamoDTO.setFechaVencimientoPrestamo(fechaDevolucion);
    prestamoDTO.setNombre(usuarioDTO.getNombre());
    prestamoDTO.setApellidos(usuarioDTO.getApellidos());
    prestamoDTO.setEmail(usuarioDTO.getEmail());
    prestamoDTO.setAutorLibro(libroDTO.getAutor());
    prestamoDTO.setTituloLibro(libroDTO.getTitulo());
    this.prestamos.add(prestamoDTO);

    return prestamoDTO;
  }


  @Override
  public void deletePrestamo(int id) {
    for (PrestamoDTO prestamo : prestamos) {
      if (prestamo.getId() == id) {
        prestamos.remove(prestamo);
        break;
      }
    }
  }


  private UsuarioDTO getUsuario(int id) {
    log.info("Buscando usuario con id: " + id + " en el servicio de usuarios: " + usuariosServiceBaseUrl);
    String url = usuariosServiceBaseUrl + "/usuarios/" + id;
    UsuarioDTO usuario = restTemplate.getForObject(url, UsuarioDTO.class);
    return usuario;
  }

  private LibroDTO getLibro(int id) {
    log.info("Buscando libro con id: " + id + " en el servicio de libros: " + librosServiceBaseUrl);
    String url = librosServiceBaseUrl + "/libros/" + id;
    LibroDTO libro = restTemplate.getForObject(url, LibroDTO.class);
    return libro;
  }
}

