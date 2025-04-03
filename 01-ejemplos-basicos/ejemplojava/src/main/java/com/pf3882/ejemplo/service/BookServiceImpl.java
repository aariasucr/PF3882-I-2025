package com.pf3882.ejemplo.service;

import com.github.javafaker.Faker;
import com.pf3882.ejemplo.dto.BookDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class BookServiceImpl implements BookService{
  private final List<BookDTO> books;

  public BookServiceImpl() {
    Faker faker = new Faker();
    this.books = new ArrayList<>();
    for(int i = 0; i < 10; i++) {
      books.add(new BookDTO(i+1, faker.book().title(), faker.book().author()));
    }
    log.info("Books list: {}", books);
  }

  @Override
  public List<BookDTO> getBooks() {
    log.info("estoy en getBooks()");
    return this.books;
  }

  @Override
  public BookDTO getBook(int id) {
    log.info("estoy en getBook() con id: {}", id);

    return books.stream().filter(book -> book.getId() == id)
      .findFirst()
      .orElse(null);
  }

  @Override
  public BookDTO addBook(BookDTO book) {
    // Generating a new ID for the book
    int newId = books.stream().mapToInt(BookDTO::getId).max().orElse(0) + 1;
    book.setId(newId);
    log.info("estoy en addBook() con id: {}", newId);
    books.add(book);
    return book;
  }

  @Override
  public BookDTO updateBook(int id, BookDTO book) {
    log.info("estoy en updateBook() con id: {}", id);
    for (BookDTO b : books) {
      if (b.getId() == id) {
        b.setTitle(book.getTitle());
        b.setAuthor(book.getAuthor());
        break;
      }
    }
    book.setId(id);
    return book;
  }

  @Override
  public void deleteBook(int id) {
    log.info("estoy en deleteBook() con id: {}", id);
    this.books.removeIf(b -> b.getId() == id);
  }
}
