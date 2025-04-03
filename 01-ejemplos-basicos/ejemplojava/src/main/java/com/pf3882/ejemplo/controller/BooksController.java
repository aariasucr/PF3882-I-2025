package com.pf3882.ejemplo.controller;

import com.pf3882.ejemplo.dto.BookDTO;
import com.pf3882.ejemplo.service.BookService;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/books")
@Tag(name="Books", description="cosas de libros")
public class BooksController {
  private final BookService bookService;

  public BooksController(BookService bookService) {
    this.bookService = bookService;
  }

  @GetMapping
  public List<BookDTO> getBooks() {
    return this.bookService.getBooks();
  }

  @GetMapping("/{id}")
  public BookDTO getBook(@PathVariable("id") int id) {
    return this.bookService.getBook(id);
  }

  @PostMapping
  public BookDTO addBook(@RequestBody BookDTO book) {
    return this.bookService.addBook(book);
  }

  @PutMapping("/{id}")
  public BookDTO updateBook(@PathVariable("id") int id, @RequestBody BookDTO book) {
    return this.bookService.updateBook(id, book);
  }

  @DeleteMapping("/{id}")
//  public void deleteBook(@PathVariable("id") int id) {
//    this.bookService.deleteBook(id);
//  }
  public ResponseEntity<?> deleteBook(@PathVariable("id") int id) {
    this.bookService.deleteBook(id);
    return ResponseEntity.noContent().build();
  }

}
