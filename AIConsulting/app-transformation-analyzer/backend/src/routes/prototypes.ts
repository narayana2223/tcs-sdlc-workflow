/**
 * Prototype Routes
 * API endpoints for transformation prototypes and examples
 */

import { Router, Request, Response } from 'express';
import { MockPrototypeService } from '../services/mock_prototype_service';

const router = Router();
const prototypeService = new MockPrototypeService();

// Get all transformation prototypes
router.get('/', async (req: Request, res: Response) => {
  try {
    const prototypes = await prototypeService.getAllPrototypes();

    res.json({
      success: true,
      data: {
        prototypes,
        total: prototypes.length
      },
      message: 'Transformation prototypes retrieved successfully'
    });
  } catch (error: any) {
    console.error('Error fetching prototypes:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch prototypes',
      details: error.message
    });
  }
});

// Get prototype by ID
router.get('/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const prototype = await prototypeService.getPrototypeById(id);

    if (!prototype) {
      return res.status(404).json({
        success: false,
        error: 'Prototype not found',
        message: `No prototype found with ID: ${id}`
      });
    }

    res.json({
      success: true,
      data: { prototype },
      message: 'Prototype retrieved successfully'
    });
  } catch (error: any) {
    console.error('Error fetching prototype:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch prototype',
      details: error.message
    });
  }
});

// Get prototypes by category
router.get('/category/:category', async (req: Request, res: Response) => {
  try {
    const { category } = req.params;
    const prototypes = await prototypeService.getPrototypesByCategory(category);

    res.json({
      success: true,
      data: {
        prototypes,
        category,
        total: prototypes.length
      },
      message: `Prototypes for category '${category}' retrieved successfully`
    });
  } catch (error: any) {
    console.error('Error fetching prototypes by category:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch prototypes by category',
      details: error.message
    });
  }
});

// Get prototypes by 12-factor
router.get('/factor/:factor', async (req: Request, res: Response) => {
  try {
    const { factor } = req.params;
    const prototypes = await prototypeService.getPrototypesByFactor(factor);

    res.json({
      success: true,
      data: {
        prototypes,
        factor,
        total: prototypes.length
      },
      message: `Prototypes for factor '${factor}' retrieved successfully`
    });
  } catch (error: any) {
    console.error('Error fetching prototypes by factor:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch prototypes by factor',
      details: error.message
    });
  }
});

// Generate custom prototype
router.post('/generate', async (req: Request, res: Response) => {
  try {
    const { factor, complexity, technology, useCase } = req.body;

    if (!factor || !complexity || !technology || !useCase) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters',
        message: 'factor, complexity, technology, and useCase are required'
      });
    }

    const customPrototype = await prototypeService.generateCustomPrototype({
      factor,
      complexity,
      technology,
      useCase
    });

    res.json({
      success: true,
      data: { prototype: customPrototype },
      message: 'Custom prototype generated successfully'
    });
  } catch (error: any) {
    console.error('Error generating custom prototype:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to generate custom prototype',
      details: error.message
    });
  }
});

// Get prototype categories and factors
router.get('/meta/info', async (req: Request, res: Response) => {
  try {
    const prototypes = await prototypeService.getAllPrototypes();

    const categories = [...new Set(prototypes.map(p => p.category))];
    const factors = [...new Set(prototypes.map(p => p.factor))];
    const complexities = ['low', 'medium', 'high'];

    const stats = {
      totalPrototypes: prototypes.length,
      categoriesCount: categories.length,
      factorsCount: factors.length
    };

    res.json({
      success: true,
      data: {
        categories,
        factors,
        complexities,
        stats
      },
      message: 'Prototype metadata retrieved successfully'
    });
  } catch (error: any) {
    console.error('Error fetching prototype metadata:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch prototype metadata',
      details: error.message
    });
  }
});

export default router;