import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App',() => {
  it('shows the app title', async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([])],
    }).compileComponents();

  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();  

  const heading: HTMLElement = fixture.nativeElement.querySelector('h1');
  expect(heading.textContent).toContain('Daily Loaf');
  });
});