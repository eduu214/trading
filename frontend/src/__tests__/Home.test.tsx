import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home', () => {
  it('renders the main heading', () => {
    render(<Home />)
    
    const heading = screen.getByRole('heading', {
      name: /FlowPlane Trading Platform/i,
    })
    
    expect(heading).toBeInTheDocument()
  })
  
  it('renders navigation links', () => {
    render(<Home />)
    
    const dashboardLink = screen.getByRole('link', { name: /Go to Dashboard/i })
    const apiLink = screen.getByRole('link', { name: /API Documentation/i })
    
    expect(dashboardLink).toBeInTheDocument()
    expect(apiLink).toBeInTheDocument()
  })
})