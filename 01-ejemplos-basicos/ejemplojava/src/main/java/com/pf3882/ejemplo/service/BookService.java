package com.pf3882.ejemplo.service;

import com.pf3882.ejemplo.dto.BookDTO;

import java.util.List;

public interface BookService {
  List<BookDTO> getBooks();
  BookDTO getBook(int id);
  BookDTO addBook(BookDTO book);
  BookDTO updateBook(int id, BookDTO book);
  void deleteBook(int id);
}
