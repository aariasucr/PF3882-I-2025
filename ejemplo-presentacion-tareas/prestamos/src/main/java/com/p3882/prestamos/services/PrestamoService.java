package com.p3882.prestamos.services;

import com.p3882.prestamos.dto.PrestamoDTO;
import com.p3882.prestamos.dto.PrestamoRequestDTO;

import java.util.List;

public interface PrestamoService {
  List<PrestamoDTO> getPrestamos();
  PrestamoDTO getPrestamo(int id);
  PrestamoDTO addPrestamo(PrestamoRequestDTO prestamoRequestDTO);
  void deletePrestamo(int id);
}
