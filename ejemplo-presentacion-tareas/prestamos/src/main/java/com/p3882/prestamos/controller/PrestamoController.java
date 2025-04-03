package com.p3882.prestamos.controller;

import com.p3882.prestamos.dto.PrestamoDTO;
import com.p3882.prestamos.dto.PrestamoRequestDTO;
import com.p3882.prestamos.services.PrestamoService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/prestamos")
@Tag(name = "Prestamos", description = "cosas de prestamos")
public class PrestamoController {
  private final PrestamoService prestamoService;

  public PrestamoController(PrestamoService prestamoService) {
    this.prestamoService = prestamoService;
  }

  @GetMapping
  public List<PrestamoDTO> getPrestamos() {
    return this.prestamoService.getPrestamos();
  }

  @GetMapping("/{id}")
  public PrestamoDTO getPrestamo(@PathVariable("id") int id) {
    return this.prestamoService.getPrestamo(id);
  }

  @PostMapping
  public PrestamoDTO addPrestamo(@RequestBody PrestamoRequestDTO prestamoRequestDTO) {
    return this.prestamoService.addPrestamo(prestamoRequestDTO);
  }

  @DeleteMapping("/{id}")
  public void deletePrestamo(@PathVariable("id") int id) {
    this.prestamoService.deletePrestamo(id);
  }
}
